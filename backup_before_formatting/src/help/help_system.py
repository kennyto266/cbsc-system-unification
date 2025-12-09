#!/usr/bin/env python3
"""
智能幫助系統核心模塊
提供完整的系統幫助、文檔查詢、教程和快速參考功能

核心功能：
1. 功能說明文檔系統
2. 使用示例展示
3. 快捷鍵支持
4. 搜索功能
5. 中英文雙語支持
"""

import json
import os
import re
import sys
import time
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime
import logging

# 導入UI系統
try:
    from src.ui.enhanced_terminal_ui import EnhancedTerminalUI
    UI_AVAILABLE = True
except ImportError:
    UI_AVAILABLE = False

logger = logging.getLogger(__name__)

@dataclass
class HelpTopic:
    """幫助主題數據結構"""
    id: str
    title: str
    category: str
    content: str
    examples: List[str]
    keywords: List[str]
    related_topics: List[str]
    difficulty: str  # "beginner", "intermediate", "advanced"
    language: str = "zh-CN"

class HelpSystem:
    """智能幫助系統核心類"""

    def __init__(self):
        self.version = "1.0.0"
        self.help_dir = Path("src/help")
        self.cache_dir = Path("cache/help")

        # 確保目錄存在
        self.help_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # 初始化UI系統
        if UI_AVAILABLE:
            self.ui = EnhancedTerminalUI()
        else:
            self.ui = None

        # 幫助主題數據
        self.topics = {}
        self.categories = {}
        self.shortcuts = {}
        self.commands = {}

        # 初始化幫助數據
        self._init_help_topics()
        self._init_categories()
        self._init_shortcuts()
        self._init_commands()

        # 搜索緩存
        self.search_cache = {}

        logger.info("幫助系統初始化完成")

    def _init_help_topics(self):
        """初始化幫助主題"""
        self.topics = {
            # 系統概覽
            "overview": HelpTopic(
                id="overview",
                title="系統概覽",
                category="system",
                content="""
香港量化交易系統是一個專業級的量化分析和交易平台，基於VectorBT框架構建。

主要特性：
• 477種技術指標計算引擎
• VectorBT專業級回測系統
• 真實港股和政府數據支持
• GPU加速計算支持
• 多策略組合優化
• Telegram機器人集成
• 風險管理系統

系統架構：
• 數據接入層：股票API + 政府數據API
• 指標計算層：CoreIndicators + TechnicalAnalyzer
• 回測執行層：VectorBTEngine + StrategyBuilder
• 用戶接口層：CLI界面 + Telegram Bot
                """.strip(),
                examples=[
                    "查看系統狀態：python interactive_quantitative_trader.py",
                    "運行集成測試：python integration_test.py"
                ],
                keywords=["系統", "概覽", "架構", "功能", "量化交易"],
                related_topics=["installation", "quick_start", "modules"],
                difficulty="beginner"
            ),

            # 安裝配置
            "installation": HelpTopic(
                id="installation",
                title="安裝與配置",
                category="system",
                content="""
系統安裝和配置步驟：

1. 基本環境要求
   • Python 3.9+
   • 建議使用虛擬環境
   • 可選：CUDA支持GPU加速

2. 核心依賴安裝
   pip install -r requirements.txt

3. 可選依賴
   pip install vectorbt  # 專業回測引擎
   pip install rich      # 美化界面
   pip install colorama  # 顏色支持

4. 配置文件
   • config/user_preferences.json - 用戶偏好設置
   • config/data_sources.yml - 數據源配置
   • config/strategies.json - 策略配置

5. 數據源設置
   系統支持真實港股數據和香港政府數據，已預配置完成。
                """.strip(),
                examples=[
                    "創建虛擬環境：python -m venv venv",
                    "激活環境：source venv/bin/activate (Linux/Mac)",
                    "安裝依賴：pip install -r requirements.txt",
                    "檢查依賴：python -m src.utils.dependency_manager"
                ],
                keywords=["安裝", "配置", "環境", "依賴", "設置"],
                related_topics=["overview", "quick_start", "data_sources"],
                difficulty="beginner"
            ),

            # 快速開始
            "quick_start": HelpTopic(
                id="quick_start",
                title="快速開始",
                category="tutorial",
                content="""
5分鐘快速上手指南：

Step 1: 啟動系統
python interactive_quantitative_trader.py

Step 2: 選擇功能
• [1] 股票數據分析 - 獲取和分析股票數據
• [2] 技術指標計算 - 計算RSI、MACD等指標
• [3] 回測系統 - 測試交易策略
• [4] 政府數據分析 - 分析經濟數據

Step 3: 基本操作示例
股票分析：
  輸入股票代碼：0700.HK
  選擇時長：252 (1年)
  查看技術指標和走勢圖

回測策略：
  選擇策略：RSI均值回歸
  設置參數：RSI周期=14, 超賣=30, 超買=70
  查看回測結果和績效指標

Step 4: 高級功能
• 批量股票分析
• 多策略組合優化
• GPU加速計算
• Telegram警報設置
                """.strip(),
                examples=[
                    "啟動系統：python interactive_quantitative_trader.py",
                    "股票分析：選擇[1] → 0700.HK → 252",
                    "策略回測：選擇[3] → RSI策略 → 查看結果"
                ],
                keywords=["快速", "開始", "入門", "教程", "示例"],
                related_topics=["overview", "modules", "strategies"],
                difficulty="beginner"
            ),

            # 模塊說明
            "modules": HelpTopic(
                id="modules",
                title="核心模塊說明",
                category="reference",
                content="""
系統包含8個核心功能模塊：

1. 股票數據分析模塊
   功能：獲取、處理、分析港股數據
   支持股票：0700.HK、0941.HK、1398.HK等所有港股
   數據源：中央API (http://18.180.162.113:9191)

2. 技術指標計算模塊
   功能：計算477種技術指標
   主要指標：RSI、MACD、布林帶、KDJ、移動平均等
   性能：GPU加速可選

3. 回測系統模塊
   功能：基於VectorBT的專業回測引擎
   支持策略：RSI、MACD、雙移動平均等6種內置策略
   指標：Sharpe比率、最大回撤、年化回報等

4. 政府數據分析模塊
   功能：香港政府經濟數據分析
   數據源：HIBOR、GDP、匯率、貨幣基礎等9個數據源
   應用：宏觀經濟分析和非價格交易策略

5. GPU加速模塊
   功能：CUDA加速的技術指標計算
   加速比：最高10x性能提升
   支持指標：RSI、MACD、布林帶等

6. 風險管理模塊
   功能：風險控制 和倉位管理
   指標：VaR、最大回撤、夏普比率等
   策略：止損、止盈、倉位限制

7. Telegram機器人模塊
   功能：實時交易信號推送
   支持功能：信號推送、倉位提醒、風險警報

8. 配置管理模塊
   功能：系統配置和偏好設置
   配置項：數據源、界面主題、語言等
                """.strip(),
                examples=[
                    "數據分析：選擇菜單[1]",
                    "指標計算：選擇菜單[2]",
                    "策略回測：選擇菜單[3]",
                    "經濟數據：選擇菜單[4]"
                ],
                keywords=["模塊", "功能", "組件", "架構"],
                related_topics=["overview", "strategies", "indicators"],
                difficulty="intermediate"
            ),

            # 技術指標詳解
            "indicators": HelpTopic(
                id="indicators",
                title="技術指標詳解",
                category="reference",
                content="""
系統支持477種技術指標，分為6大類：

1. 趨勢指標
   • SMA/EMA - 簡單/指數移動平均
   • MACD - 指數平滑異同移動平均
   • ADX - 平均趨勢指數
   • Aroon - 阿隆指標

2. 動量指標
   • RSI - 相對強弱指數
   • KDJ - 隨機指標
   • CCI - 順勢指標
   • Williams %R - 威廉指標

3. 波動率指標
   • Bollinger Bands - 布林帶
   • ATR - 平均真實波幅
   • VIX - 波動率指數

4. 成交量指標
   • Volume - 成交量
   • OBV - 量價平衡指標
   • VWAP - 成交量加權平均價

5. 價格形態
   • Candlestick - K線形態
   • Support/Resistance - 支撐阻力位
   • Chart Patterns - 圖表形態

6. 經濟數據指標
   • HIBOR相關指標
   • 貨幣基礎指標
   • 匯率相關指標
                """.strip(),
                examples=[
                    "計算RSI：indicators.calculate_rsi(data['close'], 14)",
                    "計算MACD：indicators.calculate_macd(data['close'], 12, 26, 9)",
                    "計算布林帶：indicators.calculate_bollinger_bands(data['close'], 20, 2)"
                ],
                keywords=["技術指標", "RSI", "MACD", "布林帶", "KDJ", "移動平均"],
                related_topics=["strategies", "backtesting", "calculation_methods"],
                difficulty="intermediate"
            ),

            # 交易策略詳解
            "strategies": HelpTopic(
                id="strategies",
                title="交易策略詳解",
                category="strategy",
                content="""
系統內置6種專業交易策略：

1. RSI均值回歸策略
   原理：基於RSI的超買超賣信號
   入場：RSI < 30 (超賣) 買入
   出場：RSI > 70 (超買) 賣出
   適用：震盪市場
   最佳參數：RSI周期14

2. MACD交叉策略
   原理：MACD金叉死叉信號
   入場：MACD線上穿信號線
   出場：MACD線下穿信號線
   適用：趨勢市場
   最佳參數：12,26,9

3. 布林帶策略
   原理：價格突破布林帶
   入場：價格突破上軌買入
   出場：價格跌破下軌賣出
   適用：突破策略
   最佳參數：20週期,2倍標準差

4. 雙移動平均策略
   原理：快慢均線交叉
   入場：短期均線上穿長期均線
   出場：短期均線下穿長期均線
   適用：中長期趨勢
   最佳參數：20日,50日

5. 動量突破策略
   原理：價格動量突破
   入場：動量指標突破閾值
   出場：動量衰退時
   適用：強趨勢市場

6. 波動率突破策略
   原理：波動率異常突破
   入場：波動率擴大時
   出場：波動率收縮時
   適用：高波動環境

策略組合：
• 多策略信號融合
• 動態權重分配
• 市場狀態適應
                """.strip(),
                examples=[
                    "RSI策略回測：engine.backtest_strategy(data, 'RSI_MEAN_REVERSION', params)",
                    "MACD策略：選擇菜單[3] → 選擇MACD交叉策略",
                    "策略組合：使用strategy_builder融合多個策略信號"
                ],
                keywords=["策略", "RSI", "MACD", "布林帶", "均線", "交易"],
                related_topics=["backtesting", "indicators", "optimization"],
                difficulty="intermediate"
            ),

            # 回測系統
            "backtesting": HelpTopic(
                id="backtesting",
                title="回測系統指南",
                category="tutorial",
                content="""
VectorBT專業回測系統使用指南：

回測流程：
1. 數據準備：獲取股票OHLCV數據
2. 策略定義：選擇或自定義交易策略
3. 參數設置：優化策略參數
4. 執行回測：運行回測引擎
5. 結果分析：查看績效指標

核心績效指標：
• 總回報率：策略期間內的累計收益
• Sharpe比率：風險調整後收益 (目標>1.5)
• 最大回撤：最大虧損幅度 (目標<20%)
• 年化波動率：收益波動程度
• 勝率：盈利交易占比
• 盈虧比：平均盈利/平均虧損

高級功能：
• 參數優化：自動尋找最優參數
• 多策略比較：同時測試多個策略
• 市場狀態分析：牛熊市表現差異
• 風險管理：止損止盈設置

最佳實踐：
• 使用至少3年歷史數據
• 包含完整牛熊週期
• 考慮交易成本和滑點
• 進行樣本外測試
                """.strip(),
                examples=[
                    "基礎回測：engine.backtest_strategy(data, 'RSI_MEAN_REVERSION', {'period': 14})",
                    "多策略比較：results = engine.compare_strategies(data, strategies)",
                    "參數優化：best_params = engine.optimize_parameters(data, strategy, param_ranges)"
                ],
                keywords=["回測", "VectorBT", "績效", "Sharpe", "回撤", "優化"],
                related_topics=["strategies", "risk_management", "optimization"],
                difficulty="intermediate"
            ),

            # 數據源說明
            "data_sources": HelpTopic(
                id="data_sources",
                title="數據源配置",
                category="reference",
                content="""
系統支持多種真實數據源：

1. 股票數據源
   端點：http://18.180.162.113:9191/inst/getInst
   支持：所有港股 (0700.HK, 0941.HK等)
   數據：OHLCV格式的實時歷史數據
   更新：每日收盤後更新

2. 香港政府數據源 (9個)
   • HIBOR利率：香港銀行同業拆息
   • GDP數據：本地生產總值
   • 貨幣基礎：貨幣供應量
   • 匯率數據：港幣匯率
   • 銀行流動資金：流動性指標
   • 退休基金數據：强積金數據
   • 外匯基金票据：政府債券數據
   • 人民幣流動資金：離岸人民幣數據
   • 經濟統計：綜合經濟指標

3. 數據質量保證
   100%真實官方數據
   自動數據驗證和清洗
   異常值檢測和處理
   數據完整性檢查

4. 數據存儲
   本地緩存：cache/data/
   格式：JSON、CSV、Parquet
   更新頻率：每日自動更新
                """.strip(),
                examples=[
                    "獲取股票數據：get_hk_stock_data('0700.HK', 252)",
                    "獲取HIBOR：get_hibor_data(30)",
                    "批量獲取：get_multiple_stocks(['0700.HK', '0941.HK'])"
                ],
                keywords=["數據源", "股票數據", "政府數據", "HIBOR", "GDP", "API"],
                related_topics=["government_data", "stock_data", "api_usage"],
                difficulty="intermediate"
            ),

            # 風險管理
            "risk_management": HelpTopic(
                id="risk_management",
                title="風險管理系統",
                category="advanced",
                content="""
專業風險管理和控制系統：

1. 風險指標計算
   • VaR (風險價值)：95%置信度的最大損失
   • CVaR (條件風險價值)：超過VaR的平均損失
   • 最大回撤：歷史最大虧損幅度
   • 波動率：收益率標準差
   • Beta：市場相關性風險
   • 相關性：資產間相關係數

2. 倉位管理
   • 等權重分配：均勻分散投資
   • 風險平價：等風險貢獻分配
   • 最小方差：最小化組合波動率
   • 最大夏普比率：最優風險調整收益
   • 動態調倉：定期再平衡

3. 止損止盈策略
   • 固定百分比：設定固定止損比例
   • ATR止損：基於波動率動態止損
   • 時間止損：持倉時間限制
   • 趨勢止損：技術指標信號止損

4. 壓力測試
   • 歷史情景：重現歷史危機情況
   • 蒙特卡羅：隨機情況模擬
   • 極端事件：黑天鵝事件分析

5. 合規檢查
   • 持倉限制：單股票最大倉位
   • 行業限制：行業集中度控制
   • 流動性檢查：確保可及時平倉
                """.strip(),
                examples=[
                    "計算VaR：risk.calculate_var(portfolio, confidence=0.95)",
                    "風險預警：risk.check_risk_limits(portfolio, limits)",
                    "倉位優化：risk.optimize_positions(returns, constraints)"
                ],
                keywords=["風險", "VaR", "止損", "倉位管理", "合規"],
                related_topics=["portfolio_management", "backtesting", "compliance"],
                difficulty="advanced"
            ),

            # GPU加速
            "gpu_acceleration": HelpTopic(
                id="gpu_acceleration",
                title="GPU加速計算",
                category="advanced",
                content="""
CUDA GPU加速技術指標計算：

1. 系統要求
   • NVIDIA GPU (支持CUDA)
   • CUDA Toolkit 11.0+
   • 4GB+ GPU顯存
   • cuDF、cuPy庫

2. 支持的指標
   • RSI：加速比 5-8x
   • MACD：加速比 6-10x
   • 布林帶：加速比 4-7x
   • 移動平均：加速比 8-12x
   • KDJ：加速比 5-9x

3. 性能提升
   • 大批量數據：加速效果最明顯
   • 複雜計算：GPU優勢更大
   • 並行處理：多股票同時計算
   • 內存效率：減少數據傳輸

4. 使用方法
   自動檢測GPU可用性
   自動切換GPU/CPU計算
   異常處理和降級

5. 監控指標
   • GPU使用率
   • 顯存佔用
   • 計算時間
   • 加速比
                """.strip(),
                examples=[
                    "檢查GPU：gpu_manager.check_gpu_available()",
                    "GPU指標計算：gpu_indicators.calculate_rsi_gpu(data, period)",
                    "性能測試：gpu_manager.benchmark_performance()"
                ],
                keywords=["GPU", "CUDA", "加速", "性能", "並行計算"],
                related_topics=["performance_optimization", "indicators", "technical_analysis"],
                difficulty="advanced"
            ),

            # Telegram機器人
            "telegram_bot": HelpTopic(
                id="telegram_bot",
                title="Telegram機器人",
                category="integration",
                content="""
Telegram量化交易機器人系統：

1. 功能特性
   • 實時交易信號推送
   • 倉位變化通知
   • 風險警報提醒
   • 績效報告推送
   • 交互式查詢

2. 設置步驟
   創建Telegram Bot：
     1. 聯繫@BotFather
     2. 創建新機器人
     3. 獲取Bot Token
     4. 設置Webhook或Polling

3. 配置文件
   bot_token: "YOUR_BOT_TOKEN"
   chat_id: "YOUR_CHAT_ID"
   enable_signals: true
   enable_alerts: true

4. 指令支持
   /start - 開始使用
   /help - 幫助信息
   /status - 系統狀態
   /portfolio - 倉位查詢
   /performance - 績效報告

5. 訊息格式
   📈 交易信號：股票、方向、價格
   ⚠️ 風險警報：回撤、VaR超限
   📊 績效報告：日報、週報、月報
   🔔 系統通知：異常、維護

6. 安全設置
   用戶權限控制
   訊息加密傳輸
   訪問頻率限制
                """.strip(),
                examples=[
                    "啟動機器人：python src/telegram/telegram_bot.py",
                    "發送信號：bot.send_signal('0700.HK', 'BUY', 350.0)",
                    "查詢狀態：/status 指令"
                ],
                keywords=["Telegram", "機器人", "推送", "通知", "信號"],
                related_topics=["api_integration", "alerts", "automation"],
                difficulty="intermediate"
            ),

            # 配置管理
            "configuration": HelpTopic(
                id="configuration",
                title="配置管理",
                category="system",
                content="""
系統配置管理詳解：

1. 用戶偏好設置
   config/user_preferences.json：
   {
     "default_symbol": "0700.HK",
     "default_duration": 252,
     "output_format": "table",
     "chart_type": "ascii",
     "theme": "dark",
     "language": "zh-CN",
     "auto_save_results": true
   }

2. 數據源配置
   config/data_sources.yml：
   stock_api:
     base_url: "http://18.180.162.113:9191"
     timeout: 30
     retry_count: 3

   government_data:
     hibor_source: "gov_crawler/real_data/"
     update_frequency: "daily"

3. 策略配置
   config/strategies.json：
   {
     "rsi_strategy": {
       "period": 14,
       "oversold": 30,
       "overbought": 70
     },
     "macd_strategy": {
       "fast": 12,
       "slow": 26,
       "signal": 9
     }
   }

4. 界面主題
   dark：深色主題，適合長時間使用
   light：淺色主題，明亮清晰
   colorless：無色主題，兼容性最佳

5. 動態配置
   運行時修改配置
   熱重載配置文件
   配置驗證和錯誤處理
   配置備份和恢復
                """.strip(),
                examples=[
                    "修改配置：config_manager.update_config('theme', 'dark')",
                    "保存配置：config_manager.save_config()",
                    "重置配置：config_manager.reset_to_default()"
                ],
                keywords=["配置", "設置", "偏好", "主題", "參數"],
                related_topics=["installation", "user_guide", "customization"],
                difficulty="beginner"
            ),

            # 故障排除
            "troubleshooting": HelpTopic(
                id="troubleshooting",
                title="故障排除指南",
                category="support",
                content="""
常見問題和解決方案：

1. 數據獲取問題
   問題：無法獲取股票數據
   解決：
   • 檢查網絡連接
   • 確認API端點可訪問
   • 驗證股票代碼格式
   • 檢查API限制

2. 依賴庫問題
   問題：ImportError或庫版本衝突
   解決：
   • 使用虛擬環境
   • 更新到最新版本
   • 檢查Python版本兼容性
   • 重新安裝問題庫

3. GPU問題
   問題：GPU加速不可用
   解決：
   • 檢查CUDA安裝
   • 驗證GPU驅動
   • 確認cuDF庫版本
   • 降級到CPU計算

4. 配置問題
   問題：配置文件錯誤
   解決：
   • 檢查JSON格式
   • 重置為默認配置
   • 檢查文件權限
   • 備份配置文件

5. 性能問題
   問題：計算速度慢
   解決：
   • 啟用GPU加速
   • 增加緩存大小
   • 優化數據結構
   • 使用向量化操作

6. 記憶體問題
   問題：MemoryError
   解決：
   • 減少數據量
   • 使用分批處理
   • 增加虛擬記憶體
   • 優化算法效率

日誌文件：
• interactive_trader.log
• error.log
• performance.log
                """.strip(),
                examples=[
                    "檢查依賴：python -m src.utils.dependency_manager",
                    "測試GPU：python -c 'import cupy; print(cupy.cuda.is_available())'",
                    "檢查日誌：tail -f interactive_trader.log"
                ],
                keywords=["故障", "錯誤", "問題", "調試", "日誌"],
                related_topics=["installation", "logs", "support"],
                difficulty="beginner"
            )
        }

    def _init_categories(self):
        """初始化幫助分類"""
        self.categories = {
            "system": {
                "name": "系統相關",
                "description": "系統概覽、安裝配置、環境設置",
                "icon": "⚙️"
            },
            "tutorial": {
                "name": "教程指南",
                "description": "快速入門、操作教程、最佳實踐",
                "icon": "📚"
            },
            "reference": {
                "name": "參考文檔",
                "description": "功能說明、技術指標、模塊文檔",
                "icon": "📖"
            },
            "strategy": {
                "name": "交易策略",
                "description": "策略詳解、信號生成、組合優化",
                "icon": "📈"
            },
            "advanced": {
                "name": "高級功能",
                "description": "GPU加速、風險管理、性能優化",
                "icon": "🚀"
            },
            "integration": {
                "name": "集成功能",
                "description": "Telegram機器人、API集成、自動化",
                "icon": "🔗"
            },
            "support": {
                "name": "支持幫助",
                "description": "故障排除、FAQ、聯繫支持",
                "icon": "💬"
            }
        }

    def _init_shortcuts(self):
        """初始化快捷鍵"""
        self.shortcuts = {
            # 導航快捷鍵
            "h": "help - 顯示幫助信息",
            "q": "quit - 退出程序",
            "m": "menu - 返回主菜單",
            "b": "back - 返回上一步",
            "c": "config - 配置設置",

            # 功能快捷鍵
            "1": "股票數據分析",
            "2": "技術指標計算",
            "3": "回測系統",
            "4": "政府數據分析",
            "5": "GPU加速測試",
            "6": "風險管理分析",
            "7": "Telegram機器人",
            "8": "系統配置管理",

            # 快速操作
            "sa": "stock_analysis - 快速股票分析",
            "ta": "technical_analysis - 技術分析",
            "rsi": "rsi_analysis - RSI分析",
            "macd": "macd_analysis - MACD分析",
            "bb": "bollinger_bands - 布林帶分析",

            # 系統命令
            "status": "查看系統狀態",
            "deps": "檢查依賴狀態",
            "clear": "清屏",
            "reset": "重置系統"
        }

    def _init_commands(self):
        """初始化命令別名"""
        self.commands = {
            # 完整命令對應
            "help": ["h", "?", "幫助"],
            "quit": ["q", "exit", "退出", "quit()"],
            "menu": ["m", "main", "主菜單", "home"],
            "back": ["b", "return", "返回", "上一頁"],
            "config": ["c", "settings", "設置", "配置"],
            "status": ["st", "系統狀態", "狀態"],
            "clear": ["cls", "清屏", "clean"],
            "deps": ["dependencies", "依賴", "依賴檢查"],
            "reset": ["restart", "重置", "重新開始"],

            # 功能命令
            "stock": ["stock_analysis", "sa", "股票", "股票分析"],
            "indicator": ["ta", "technical", "指標", "技術分析"],
            "backtest": ["bt", "test", "回測", "測試"],
            "government": ["gov", "macro", "政府", "宏觀"],
            "gpu": ["gpu_test", "acceleration", "GPU", "加速"],
            "risk": ["risk_mgmt", "風險", "風控"],
            "telegram": ["bot", "tg", "機器人"],

            # 策略命令
            "rsi": ["rsi_strategy", "RSI"],
            "macd": ["macd_strategy", "MACD"],
            "bb": ["bollinger", "布林帶", "BB"],
            "ma": ["moving_average", "均線"],
            "sma": ["sma_strategy", "簡單均線"],
            "ema": ["ema_strategy", "指數均線"],

            # 數據命令
            "data": ["數據", "data"],
            "cache": ["緩存", "cache"],
            "export": ["導出", "export"],
            "import": ["導入", "import"],
            "save": ["保存", "save"],
            "load": ["加載", "load"]
        }

    def search_help(self, query: str, max_results: int = 10) -> List[HelpTopic]:
        """搜索幫助主題"""
        query = query.lower().strip()

        # 檢查緩存
        cache_key = f"{query}_{max_results}"
        if cache_key in self.search_cache:
            return self.search_cache[cache_key]

        results = []

        # 精確匹配
        for topic_id, topic in self.topics.items():
            if query == topic_id.lower() or query in [k.lower() for k in topic.keywords]:
                results.append((100, topic))  # 最高權重

        # 標題匹配
        for topic_id, topic in self.topics.items():
            if query in topic.title.lower():
                if topic not in [r[1] for r in results]:
                    results.append((80, topic))

        # 內容匹配
        for topic_id, topic in self.topics.items():
            if query in topic.content.lower():
                if topic not in [r[1] for r in results]:
                    results.append((60, topic))

        # 關鍵詞匹配
        for topic_id, topic in self.topics.items():
            for keyword in topic.keywords:
                if query in keyword.lower():
                    if topic not in [r[1] for r in results]:
                        results.append((40, topic))
                    break

        # 分類匹配
        for category_id, category_info in self.categories.items():
            if query in category_info["name"].lower() or query in category_info["description"].lower():
                for topic_id, topic in self.topics.items():
                    if topic.category == category_id and topic not in [r[1] for r in results]:
                        results.append((20, topic))

        # 排序並限制結果數量
        results.sort(key=lambda x: x[0], reverse=True)
        final_results = [topic for score, topic in results[:max_results]]

        # 緩存結果
        self.search_cache[cache_key] = final_results

        return final_results

    def get_topic(self, topic_id: str) -> Optional[HelpTopic]:
        """獲取特定幫助主題"""
        return self.topics.get(topic_id)

    def get_topics_by_category(self, category: str) -> List[HelpTopic]:
        """根據分類獲取主題"""
        return [topic for topic in self.topics.values() if topic.category == category]

    def get_topic_suggestions(self, query: str) -> List[str]:
        """獲取主題建議"""
        suggestions = []
        query = query.lower()

        for topic_id, topic in self.topics.items():
            # ID匹配
            if query in topic_id.lower():
                suggestions.append(topic_id)
                continue

            # 標題匹配
            if query in topic.title.lower():
                suggestions.append(topic_id)
                continue

            # 關鍵詞匹配
            for keyword in topic.keywords:
                if query in keyword.lower():
                    suggestions.append(topic_id)
                    break

        return suggestions[:5]  # 最多5個建議

    def expand_command(self, command: str) -> str:
        """展開命令別名"""
        command = command.lower().strip()

        for full_cmd, aliases in self.commands.items():
            if command in [alias.lower() for alias in aliases]:
                return full_cmd

        return command

    def get_shortcut_help(self, shortcut: str) -> Optional[str]:
        """獲取快捷鍵說明"""
        return self.shortcuts.get(shortcut.lower())

    def show_all_shortcuts(self) -> Dict[str, str]:
        """顯示所有快捷鍵"""
        return self.shortcuts

    def get_related_topics(self, topic_id: str) -> List[HelpTopic]:
        """獲取相關主題"""
        topic = self.get_topic(topic_id)
        if not topic or not topic.related_topics:
            return []

        related = []
        for related_id in topic.related_topics:
            if related_id in self.topics:
                related.append(self.topics[related_id])

        return related

    def get_tutorial_sequence(self) -> List[str]:
        """獲取推薦的學習路徑"""
        return [
            "overview",
            "installation",
            "quick_start",
            "modules",
            "indicators",
            "strategies",
            "backtesting",
            "risk_management",
            "gpu_acceleration",
            "telegram_bot"
        ]

    def get_beginner_topics(self) -> List[HelpTopic]:
        """獲取初學者主題"""
        return [topic for topic in self.topics.values() if topic.difficulty == "beginner"]

    def get_advanced_topics(self) -> List[HelpTopic]:
        """獲取高級主題"""
        return [topic for topic in self.topics.values() if topic.difficulty == "advanced"]

    def get_faq_topics(self) -> List[HelpTopic]:
        """獲取FAQ主題"""
        faq_keywords = ["故障", "錯誤", "問題", "常見", "FAQ"]
        faq_topics = []

        for topic in self.topics.values():
            if any(keyword in topic.title for keyword in faq_keywords) or \
               any(keyword in " ".join(topic.keywords) for keyword in faq_keywords):
                faq_topics.append(topic)

        return faq_topics

    def format_help_output(self, topic: HelpTopic) -> str:
        """格式化幫助輸出"""
        output = []

        # 標題
        output.append(f"\n🔍 {topic.title}")
        output.append("=" * (len(topic.title) + 3))

        # 分類和難度
        category_info = self.categories.get(topic.category, {"name": topic.category})
        output.append(f"📂 分類: {category_info['name']} | 📊 難度: {topic.difficulty}")

        # 內容
        output.append(f"\n📝 說明:")
        output.append(topic.content)

        # 關鍵詞
        if topic.keywords:
            output.append(f"\n🏷️ 關鍵詞: {', '.join(topic.keywords)}")

        # 示例
        if topic.examples:
            output.append(f"\n💡 使用示例:")
            for i, example in enumerate(topic.examples, 1):
                output.append(f"   {i}. {example}")

        # 相關主題
        related = self.get_related_topics(topic.id)
        if related:
            output.append(f"\n🔗 相關主題:")
            for related_topic in related:
                output.append(f"   • {related_topic.title} (使用: help {related_topic.id})")

        return "\n".join(output)

    def show_category_overview(self) -> str:
        """顯示分類概覽"""
        output = []
        output.append("\n📚 幫助系統分類")
        output.append("=" * 20)

        for category_id, category_info in self.categories.items():
            topics = self.get_topics_by_category(category_id)
            topic_count = len(topics)

            output.append(f"\n{category_info['icon']} {category_info['name']} ({topic_count}個主題)")
            output.append(f"   {category_info['description']}")

            if topics:
                output.append("   主題:")
                for topic in topics[:5]:  # 最多顯示5個
                    output.append(f"   • {topic.title} (help {topic.id})")
                if len(topics) > 5:
                    output.append(f"   • ... 還有{len(topics)-5}個主題")

        return "\n".join(output)

    def save_help_cache(self):
        """保存幫助緩存"""
        try:
            cache_file = self.cache_dir / "help_cache.json"
            cache_data = {
                "search_cache": self.search_cache,
                "timestamp": datetime.now().isoformat(),
                "version": self.version
            }

            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)

        except Exception as e:
            logger.warning(f"保存幫助緩存失敗: {e}")

    def load_help_cache(self):
        """加載幫助緩存"""
        try:
            cache_file = self.cache_dir / "help_cache.json"
            if cache_file.exists():
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                    self.search_cache = cache_data.get("search_cache", {})

        except Exception as e:
            logger.warning(f"加載幫助緩存失敗: {e}")

    def generate_help_report(self) -> Dict[str, Any]:
        """生成幫助系統報告"""
        return {
            "total_topics": len(self.topics),
            "total_categories": len(self.categories),
            "total_shortcuts": len(self.shortcuts),
            "cache_size": len(self.search_cache),
            "topics_by_category": {
                cat_id: len(self.get_topics_by_category(cat_id))
                for cat_id in self.categories.keys()
            },
            "difficulty_distribution": {
                "beginner": len(self.get_beginner_topics()),
                "intermediate": len([t for t in self.topics.values() if t.difficulty == "intermediate"]),
                "advanced": len(self.get_advanced_topics())
            },
            "version": self.version,
            "last_updated": datetime.now().isoformat()
        }

if __name__ == "__main__":
    # 簡單測試
    help_system = HelpSystem()

    # 測試搜索
    results = help_system.search_help("RSI")
    print(f"搜索'RSI'找到 {len(results)} 個結果")

    # 顯示分類概覽
    print(help_system.show_category_overview())

    # 生成報告
    report = help_system.generate_help_report()
    print(f"幫助系統報告: {report}")