#!/usr/bin/env python3
"""
互動式教程系統
提供step-by-step的新手引導和高級功能教程

核心功能：
1. 新手引導模式
2. 功能導航和介紹
3. 實操練習
4. 進度跟踪
5. 自適應學習路徑
"""

import sys
import time
import json
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
class TutorialStep:
    """教程步驟數據結構"""
    step_id: str
    title: str
    content: str
    action_type: str  # "info", "input", "command", "exercise", "quiz"
    action_data: Any
    expected_result: str
    hints: List[str]
    next_step: Optional[str] = None
    alternative_steps: List[str] = None

@dataclass
class TutorialProgress:
    """教程進度數據結構"""
    user_id: str
    tutorial_id: str
    current_step: str
    completed_steps: List[str]
    start_time: datetime
    last_activity: datetime
    score: float = 0.0
    hints_used: int = 0
    time_spent: float = 0.0  # 分鐘

class InteractiveTutorial:
    """互動式教程系統"""

    def __init__(self):
        self.version = "1.0.0"
        self.tutorial_dir = Path("src/help")
        self.progress_dir = Path("cache/tutorials")

        # 確保目錄存在
        self.tutorial_dir.mkdir(parents=True, exist_ok=True)
        self.progress_dir.mkdir(parents=True, exist_ok=True)

        # 初始化UI系統
        if UI_AVAILABLE:
            self.ui = EnhancedTerminalUI()
        else:
            self.ui = None

        # 教程數據
        self.tutorials = {}
        self.current_user = "default_user"
        self.current_progress = None

        # 初始化教程
        self._init_tutorials()

        logger.info("互動式教程系統初始化完成")

    def _init_tutorials(self):
        """初始化教程內容"""
        self.tutorials = {
            # 新手入門教程
            "beginner_guide": {
                "id": "beginner_guide",
                "title": "新手入門完全指南",
                "description": "從零開始學習量化交易系統的使用",
                "difficulty": "beginner",
                "estimated_time": 30,  # 分鐘
                "prerequisites": [],
                "steps": self._create_beginner_steps()
            },

            # 快速入門教程
            "quick_start": {
                "id": "quick_start",
                "title": "5分鐘快速上手",
                "description": "快速掌握系統核心功能",
                "difficulty": "beginner",
                "estimated_time": 5,
                "prerequisites": [],
                "steps": self._create_quick_start_steps()
            },

            # 技術分析教程
            "technical_analysis": {
                "id": "technical_analysis",
                "title": "技術指標深度解析",
                "description": "掌握技術指標的計算和應用",
                "difficulty": "intermediate",
                "estimated_time": 45,
                "prerequisites": ["beginner_guide"],
                "steps": self._create_technical_analysis_steps()
            },

            # 回測策略教程
            "backtesting_master": {
                "id": "backtesting_master",
                "title": "策略回測大師班",
                "description": "專業級策略回測和優化技巧",
                "difficulty": "intermediate",
                "estimated_time": 60,
                "prerequisites": ["technical_analysis"],
                "steps": self._create_backtesting_steps()
            },

            # 高級功能教程
            "advanced_features": {
                "id": "advanced_features",
                "title": "高級功能探索",
                "description": "GPU加速、風險管理、自動化等高級功能",
                "difficulty": "advanced",
                "estimated_time": 90,
                "prerequisites": ["backtesting_master"],
                "steps": self._create_advanced_steps()
            },

            # 實戰案例教程
            "real_world_examples": {
                "id": "real_world_examples",
                "title": "實戰案例分析",
                "description": "基於真實市場數據的量化交易案例",
                "difficulty": "advanced",
                "estimated_time": 120,
                "prerequisites": ["backtesting_master"],
                "steps": self._create_real_world_steps()
            }
        }

    def _create_beginner_steps(self) -> Dict[str, TutorialStep]:
        """創建新手教程步驟"""
        return {
            "welcome": TutorialStep(
                step_id="welcome",
                title="歡迎來到量化交易世界",
                content="""
🎉 歡迎使用香港量化交易系統！

這是一個專業級的量化分析和交易平台，讓你能夠：
• 分析真實港股數據
• 計算477種技術指標
• 回測交易策略
• 優化投資組合

在接下來的30分鐘裡，我將帶你逐步掌握系統的核心功能。

準備好了嗎？讓我們開始這段精彩的量化交易之旅！
                """.strip(),
                action_type="input",
                action_data={"prompt": "準備好了嗎？(輸入 'yes' 開始)", "expected": ["yes", "y", "準備好了", "開始"]},
                expected_result="開始學習之旅",
                hints=["只需要輸入 'yes' 即可開始"]
            ),

            "system_overview": TutorialStep(
                step_id="system_overview",
                title="系統架構概覽",
                content="""
🏗️ 讓我們了解系統的基本架構：

數據接入層：獲取真實港股和政府數據
⬇️
指標計算層：計算477種技術指標
⬇️
回測執行層：基於VectorBT的策略回測
⬇️
用戶接口層：CLI界面和Telegram機器人

系統擁有以下核心模塊：
1. 股票數據分析
2. 技術指標計算
3. 回測系統
4. 政府數據分析
5. GPU加速
6. 風險管理
7. Telegram機器人
8. 配置管理

現在讓我們啟動系統看看實際界面！
                """.strip(),
                action_type="command",
                action_data={"command": "python interactive_quantitative_trader.py", "description": "啟動量化交易系統"},
                expected_result="看到系統主菜單，包含8個功能選項",
                hints=["確保在正確的目錄中運行命令", "如果看到錯誤，檢查Python環境"]
            ),

            "first_analysis": TutorialStep(
                step_id="first_analysis",
                title="第一次股票分析",
                content="""
📊 現在讓我們進行第一次股票分析！

我們將分析騰訊控股 (0700.HK) 的數據，這是香港交易所的明星股票。

步驟：
1. 在主菜單中選擇 [1] 股票數據分析
2. 輸入股票代碼：0700.HK
3. 選擇數據時長：252 (約1年)
4. 查看分析結果

你將看到：
• 基本統計信息 (股價範圍、波動率等)
• 技術指標 (RSI、MACD等)
• 價格走勢圖
• 成交量分析
                """.strip(),
                action_type="exercise",
                action_data={
                    "task": "分析0700.HK股票數據",
                    "steps": [
                        "選擇菜單 [1]",
                        "輸入 0700.HK",
                        "輸入 252",
                        "查看結果"
                    ]
                },
                expected_result="成功顯示騰訊股票的分析報告",
                hints=["股票代碼格式很重要：0700.HK", "252代表約1年的交易日"]
            ),

            "understanding_indicators": TutorialStep(
                step_id="understanding_indicators",
                title="理解技術指標",
                content="""
📈 讓我們學習最重要的技術指標：

RSI (相對強弱指數)：
• 範圍：0-100
• <30：超賣信號 (可能上漲)
• >70：超買信號 (可能下跌)

MACD (指數平滑異同移動平均)：
• 快線：短期趨勢
• 慢線：長期趨勢
• 金叉：快線上穿慢線 (買入信號)
• 死叉：快線下穿慢線 (賣出信號)

移動平均線：
• SMA：簡單移動平均
• EMA：指數移動平均
• 金叉死叉：判斷趨勢轉換

現在讓我們計算一些具體的指標！
                """.strip(),
                action_type="exercise",
                action_data={
                    "task": "查看騰訊股票的技術指標",
                    "focus": ["RSI", "MACD", "移動平均線"],
                    "questions": [
                        "當前RSI值是多少？",
                        "MACD線和信號線的位置關係？",
                        "股價在均線上方還是下方？"
                    ]
                },
                expected_result="能夠識別和讀懂主要技術指標",
                hints=["RSI接近30表示超賣，接近70表示超買", "MACD金叉是好信號"]
            ),

            "first_backtest": TutorialStep(
                step_id="first_backtest",
                title="第一次策略回測",
                content="""
🎯 現在是最激動人心的部分 - 測試交易策略！

我們將使用RSI均值回歸策略，這是一個經典的策略：

策略邏輯：
• RSI < 30：買入 (超賣反彈)
• RSI > 70：賣出 (超買回調)

步驟：
1. 返回主菜單
2. 選擇 [3] 回測系統
3. 選擇 RSI均值回歸策略
4. 使用默認參數 (RSI=14, 超賣=30, 超買=70)
5. 選擇0700.HK進行回測

重點關注指標：
• 總回報率：策略收益
• Sharpe比率：風險調整後收益 (>1.5算好)
• 最大回撤：最大虧損幅度 (<20%算可接受)
• 勝率：盈利交易比例
                """.strip(),
                action_type="exercise",
                action_data={
                    "task": "執行RSI策略回測",
                    "strategy": "RSI均值回歸",
                    "parameters": {"period": 14, "oversold": 30, "overbought": 70},
                    "symbol": "0700.HK"
                },
                expected_result="獲得完整的回測報告，包含績效指標",
                hints=[" Sharpe比率 > 1.5 表示策略不錯", "最大回撤越小越好"]
            ),

            "data_sources": TutorialStep(
                step_id="data_sources",
                title="了解數據源",
                content="""
🌐 了解我們的數據源：

股票數據源：
• 來源：中央API (http://18.180.162.113:9191)
• 內容：真實港股OHLCV數據
• 覆蓋：所有港股
• 更新：每日收盤後

香港政府數據源 (9個)：
1. HIBOR利率 - 香港銀行同業拆息
2. GDP數據 - 本地生產總值
3. 貨幣基礎 - 貨幣供應量
4. 匯率數據 - 港幣兌換率
5. 銀行流動資金
6. 退休基金
7. 外匯基金票據
8. 人民幣流動資金
9. 經濟統計數據

所有數據都是100%真實的官方數據！

讓我們查看一些政府數據：
                """.strip(),
                action_type="exercise",
                action_data={
                    "task": "查看香港政府經濟數據",
                    "steps": [
                        "返回主菜單",
                        "選擇 [4] 政府數據分析",
                        "選擇HIBOR利率數據",
                        "查看最近的利率走勢"
                    ]
                },
                expected_result="成功查看政府經濟數據",
                hints=["政府數據可以幫助判斷宏觀經濟環境", "HIBOR利率影響股市表現"]
            ),

            "risk_management": TutorialStep(
                step_id="risk_management",
                title="風險管理基礎",
                content="""
⚠️ 學習風險管理非常重要：

主要風險指標：
1. 最大回撤 (Max Drawdown)
   • 含義：歷史最大虧損幅度
   • 目標：< 20%

2. Sharpe比率
   • 含義：風險調整後收益
   • 目標：> 1.5

3. 波動率 (Volatility)
   • 含義：收益率波動程度
   • 越低越穩定

風險控制方法：
• 分散投資
• 設置止損
• 控制倉位大小
• 定期調倉

讓我們檢查系統的風險管理功能：
                """.strip(),
                action_type="info",
                action_data={"focus": "風險指標意義和重要性"},
                expected_result="理解主要風險指標",
                hints=["高收益通常伴隨高風險", "不要把所有雞蛋放在一個籃子裡"]
            ),

            "configuration": TutorialStep(
                step_id="configuration",
                title="個性化配置",
                content="""
⚙️ 學習配置系統：

主要配置項：
• 默認股票：0700.HK
• 數據時長：252天
• 界面主題：dark/light
• 語言：中文/英文
• 輸出格式：table/json
• 自動保存：true/false

配置文件位置：
• config/user_preferences.json

讓我們嘗試修改配置：
                """.strip(),
                action_type="exercise",
                action_data={
                    "task": "修改系統配置",
                    "steps": [
                        "返回主菜單",
                        "選擇 [8] 系統配置管理",
                        "嘗試修改界面主題",
                        "保存配置"
                    ]
                },
                expected_result="成功修改並保存配置",
                hints=["配置會即時生效", "可以隨時重置為默認值"]
            ),

            "next_steps": TutorialStep(
                step_id="next_steps",
                title="後續學習路徑",
                content="""
🎓 恭喜完成新手教程！

你已經掌握了：
✅ 系統基本操作
✅ 股票數據分析
✅ 技術指標理解
✅ 策略回測
✅ 數據源了解
✅ 風險管理基礎
✅ 系統配置

推薦後續學習路徑：

1. 📚 技術分析深入教程
   • 深入學習477種技術指標
   • 指標組合使用技巧
   • 不同市場環境下的指標選擇

2. 🎯 策略回測大師班
   • 高級回測技巧
   • 參數優化方法
   • 多策略組合

3. 🚀 高級功能探索
   • GPU加速計算
   • 自動化交易
   • Telegram機器人

4. 💼 實戰案例分析
   • 真實市場案例
   • 策略實踐應用
   • 性能優化技巧

繼續加油，成為量化交易大師！
                """.strip(),
                action_type="info",
                action_data={"recommendations": ["technical_analysis", "backtesting_master", "advanced_features"]},
                expected_result="了解後續學習方向",
                hints=["按照難度循序漸進學習", "多實踐，多總結"]
            )
        }

    def _create_quick_start_steps(self) -> Dict[str, TutorialStep]:
        """創建快速入門步驟"""
        return {
            "start": TutorialStep(
                step_id="start",
                title="5分鐘快速上手",
                content="""
⚡ 讓我們在5分鐘內掌握系統核心功能！

步驟1: 啟動系統
python interactive_quantitative_trader.py

步驟2: 快速分析 (1分鐘)
• 選 [1] 股票數據分析
• 輸入 0700.HK
• 輸入 365 (1年數據)

步驟3: 查看回測 (2分鐘)
• 選 [3] 回測系統
• 選 RSI均值回歸策略
• 使用默認參數

步驟4: 查看績效 (1分鐘)
• 關注Sharpe比率 (目標>1.5)
• 關注最大回撤 (目標<20%)
• 關注總回報率

開始吧！
                """.strip(),
                action_type="command",
                action_data={"command": "python interactive_quantitative_trader.py"},
                expected_result="啟動系統並完成一次完整的分析流程",
                hints=["按照提示一步步操作", "不需要深入理解每個細節"]
            )
        }

    def _create_technical_analysis_steps(self) -> Dict[str, TutorialStep]:
        """創建技術分析教程步驟"""
        return {
            "indicator_basics": TutorialStep(
                step_id="indicator_basics",
                title="技術指標基礎",
                content="""
📊 深入學習技術指標：

趨勢指標：
• SMA/EMA：判斷趨勢方向
• MACD：趨勢轉換信號
• ADX：趨勢強弱度量

動量指標：
• RSI：超買超賣判斷
• KDJ：隨機波動分析
• CCI：價格偏離度

波動率指標：
• 布林帶：價格通道
• ATR：真實波幅
• VIX：波動率指數

讓我們實際計算這些指標：
                """.strip(),
                action_type="exercise",
                action_data={
                    "task": "計算多種技術指標",
                    "indicators": ["RSI", "MACD", "布林帶", "ATR"],
                    "symbol": "0700.HK"
                },
                expected_result="成功計算並理解多種技術指標",
                hints=["不同指標適用不同市場環境", "需要綜合使用多個指標"]
            )
        }

    def _create_backtesting_steps(self) -> Dict[str, TutorialStep]:
        """創建回測教程步驟"""
        return {
            "advanced_backtesting": TutorialStep(
                step_id="advanced_backtesting",
                title="高級回測技巧",
                content="""
🎯 專業級回測技術：

1. 參數優化
   • 網格搜索
   • 貝葉斯優化
   • 遺傳算法

2. 樣本外測試
   • Walk-forward分析
   • 時間序列分割
   • 交叉驗證

3. 多策略比較
   • 績效指標對比
   • 風險調整收益
   • 相關性分析

4. 市場狀態分析
   • 牛熊市表現
   • 波動率環境
   - 經濟週期影響

讓我們實踐這些技巧：
                """.strip(),
                action_type="exercise",
                action_data={
                    "task": "執行高級回測分析",
                    "techniques": ["parameter_optimization", "walk_forward", "multi_strategy"],
                    "tools": ["vectorbt_optimizer", "strategy_builder"]
                },
                expected_result="掌握專業級回測技巧",
                hints=["避免過度擬合", "確保統計顯著性"]
            )
        }

    def _create_advanced_steps(self) -> Dict[str, TutorialStep]:
        """創建高級功能教程步驟"""
        return {
            "gpu_acceleration": TutorialStep(
                step_id="gpu_acceleration",
                title="GPU加速計算",
                content="""
🚀 CUDA GPU加速技術：

系統要求：
• NVIDIA GPU (支持CUDA)
• CUDA Toolkit 11.0+
• cuDF、cuPy庫

加速效果：
• RSI計算：5-8x
• MACD計算：6-10x
• 布林帶：4-7x
• 大批量：10x+

讓我們測試GPU加速：
                """.strip(),
                action_type="exercise",
                action_data={
                    "task": "測試GPU加速性能",
                    "steps": [
                        "檢查GPU可用性",
                        "對比CPU/GPU性能",
                        "分析加速效果"
                    ]
                },
                expected_result="成功啟用GPU加速",
                hints=["GPU需要正確配置CUDA環境", "大批量計算時效果最明顯"]
            )
        }

    def _create_real_world_steps(self) -> Dict[str, TutorialStep]:
        """創建實戰案例步驟"""
        return {
            "case_study": TutorialStep(
                step_id="case_study",
                title="實戰案例：2024年港股分析",
                content="""
💼 真實市場案例分析：

案例背景：
• 2024年香港股市波動加劇
• 中美關係影響市場情緒
• 科技股表現分化

分析任務：
1. 市場環境分析
2. 行業輪動研究
3. 個股機會挖掘
4. 風險評估控制

讓我們開始實戰分析：
                """.strip(),
                action_type="exercise",
                action_data={
                    "task": "2024年港股實戰分析",
                    "stocks": ["0700.HK", "0941.HK", "1398.HK"],
                    "timeframe": "2024-01-01 to 2024-12-31",
                    "analysis": ["technical", "fundamental", "risk"]
                },
                expected_result="完成一份完整的實戰分析報告",
                hints=["結合宏觀經濟分析", "關注行業政策變化"]
            )
        }

    def start_tutorial(self, tutorial_id: str, user_id: str = "default_user") -> bool:
        """開始教程"""
        if tutorial_id not in self.tutorials:
            return False

        # 檢查前置條件
        tutorial = self.tutorials[tutorial_id]
        if tutorial["prerequisites"]:
            for prereq in tutorial["prerequisites"]:
                if not self._is_tutorial_completed(prereq, user_id):
                    print(f"⚠️  需要先完成前置教程：{self.tutorials[prereq]['title']}")
                    return False

        # 創建進度記錄
        self.current_user = user_id
        self.current_progress = TutorialProgress(
            user_id=user_id,
            tutorial_id=tutorial_id,
            current_step="welcome",
            completed_steps=[],
            start_time=datetime.now(),
            last_activity=datetime.now()
        )

        # 開始教程
        return self._execute_tutorial()

    def _execute_tutorial(self) -> bool:
        """執行教程流程"""
        tutorial_id = self.current_progress.tutorial_id
        tutorial = self.tutorials[tutorial_id]

        print(f"\n🎓 {tutorial['title']}")
        print(f"⏱️  預計時間：{tutorial['estimated_time']}分鐘")
        print(f"📊 難度：{tutorial['difficulty']}")
        print("=" * 50)

        current_step_id = self.current_progress.current_step
        while current_step_id:
            step = tutorial["steps"].get(current_step_id)
            if not step:
                break

            # 顯示步驟內容
            self._display_step(step)

            # 執行步驟動作
            success = self._execute_step_action(step)
            if not success:
                print(f"❌ 步驟 {step.title} 執行失敗")
                return False

            # 更新進度
            self.current_progress.completed_steps.append(current_step_id)
            self.current_progress.last_activity = datetime.now()

            # 決定下一步
            if step.next_step:
                current_step_id = step.next_step
            else:
                current_step_id = None

        # 教程完成
        self._complete_tutorial()
        return True

    def _display_step(self, step: TutorialStep):
        """顯示教程步驟"""
        print(f"\n📍 {step.title}")
        print("-" * (len(step.title) + 3))
        print(step.content)

    def _execute_step_action(self, step: TutorialStep) -> bool:
        """執行步驟動作"""
        if step.action_type == "info":
            input("\n按回車鍵繼續...")
            return True

        elif step.action_type == "input":
            return self._handle_input_step(step)

        elif step.action_type == "command":
            return self._handle_command_step(step)

        elif step.action_type == "exercise":
            return self._handle_exercise_step(step)

        elif step.action_type == "quiz":
            return self._handle_quiz_step(step)

        return True

    def _handle_input_step(self, step: TutorialStep) -> bool:
        """處理輸入步驟"""
        prompt = step.action_data["prompt"]
        expected = step.action_data["expected"]

        while True:
            user_input = input(f"\n{prompt}: ").strip().lower()

            if any(exp in user_input for exp in expected):
                print(f"✅ {step.expected_result}")
                return True

            print("❌ 請重新輸入")
            if step.hints:
                print(f"💡 提示：{step.hints[0]}")

    def _handle_command_step(self, step: TutorialStep) -> bool:
        """處理命令步驟"""
        command = step.action_data["command"]
        description = step.action_data.get("description", "")

        print(f"\n💻 請執行以下命令：")
        print(f"命令：{command}")
        if description:
            print(f"說明：{description}")

        # 這裡不能自動執行命令，需要用戶手動執行
        input("執行完畢後按回車鍵繼續...")

        # 模擬驗證結果
        print(f"✅ {step.expected_result}")
        return True

    def _handle_exercise_step(self, step: TutorialStep) -> bool:
        """處理練習步驟"""
        task = step.action_data["task"]
        steps = step.action_data.get("steps", [])

        print(f"\n🎯 實踐任務：{task}")

        if steps:
            print("步驟：")
            for i, s in enumerate(steps, 1):
                print(f"  {i}. {s}")

        # 交互式指導
        if step.hints:
            print(f"\n💡 提示：{step.hints[0]}")

        # 等待用戶完成
        user_ready = input("\n完成任務後輸入 'done' 繼續: ").strip().lower()

        if user_ready in ["done", "完成", "ok"]:
            print(f"✅ {step.expected_result}")
            return True
        else:
            # 提供更多幫助
            print("🤓 需要更多幫助嗎？")
            help_needed = input("輸入 'help' 獲取詳細指導: ").strip().lower()
            if help_needed in ["help", "幫助"]:
                self._provide_exercise_help(step)
            return self._handle_exercise_step(step)  # 重試

    def _handle_quiz_step(self, step: TutorialStep) -> bool:
        """處理測驗步驟"""
        # 這裡可以實現測驗邏輯
        print("\n📝 小測驗")
        print("（測驗功能開發中...）")
        input("按回車鍵繼續...")
        return True

    def _provide_exercise_help(self, step: TutorialStep):
        """提供練習幫助"""
        print("\n🆘 詳細指導：")

        if hasattr(step, 'hints') and len(step.hints) > 1:
            for hint in step.hints[1:]:
                print(f"• {hint}")

        # 可以根據具體步驟提供更有針對性的幫助
        if step.step_id == "first_analysis":
            print("\n詳細步驟：")
            print("1. 確保你已經運行了 'python interactive_quantitative_trader.py'")
            print("2. 在顯示的菜單中輸入數字 '1' 然後按回車")
            print("3. 輸入股票代碼：0700.HK (注意格式)")
            print("4. 輸入數據天數：252")
            print("5. 等待分析結果顯示")

    def _is_tutorial_completed(self, tutorial_id: str, user_id: str) -> bool:
        """檢查教程是否已完成"""
        progress_file = self.progress_dir / f"{user_id}_{tutorial_id}.json"
        return progress_file.exists()

    def _complete_tutorial(self):
        """完成教程"""
        if not self.current_progress:
            return

        # 計算學習時間
        end_time = datetime.now()
        time_spent = (end_time - self.current_progress.start_time).total_seconds() / 60  # 分鐘
        self.current_progress.time_spent = time_spent

        # 計算分數 (簡化版本)
        total_steps = len(self.tutorials[self.current_progress.tutorial_id]["steps"])
        completed_steps = len(self.current_progress.completed_steps)
        self.current_progress.score = (completed_steps / total_steps) * 100

        # 保存進度
        self._save_progress()

        # 顯示完成信息
        self._show_completion_certificate()

    def _save_progress(self):
        """保存教程進度"""
        if not self.current_progress:
            return

        progress_file = self.progress_dir / f"{self.current_progress.user_id}_{self.current_progress.tutorial_id}.json"

        progress_data = {
            "user_id": self.current_progress.user_id,
            "tutorial_id": self.current_progress.tutorial_id,
            "current_step": self.current_progress.current_step,
            "completed_steps": self.current_progress.completed_steps,
            "start_time": self.current_progress.start_time.isoformat(),
            "last_activity": self.current_progress.last_activity.isoformat(),
            "score": self.current_progress.score,
            "hints_used": self.current_progress.hints_used,
            "time_spent": self.current_progress.time_spent,
            "completed": True
        }

        try:
            with open(progress_file, 'w', encoding='utf-8') as f:
                json.dump(progress_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存教程進度失敗: {e}")

    def _show_completion_certificate(self):
        """顯示完成證書"""
        tutorial_id = self.current_progress.tutorial_id
        tutorial = self.tutorials[tutorial_id]

        print("\n" + "="*60)
        print("🎓 教程完成證書")
        print("="*60)
        print(f"✅ 教程：{tutorial['title']}")
        print(f"👤 學員：{self.current_progress.user_id}")
        print(f"⏱️  學習時間：{self.current_progress.time_spent:.1f} 分鐘")
        print(f"📊 完成度：{self.current_progress.score:.1f}%")
        print(f"🎯 難度：{tutorial['difficulty']}")
        print("="*60)
        print("🌟 繼續努力，成為量化交易大師！")
        print("="*60)

    def get_tutorial_list(self) -> List[Dict]:
        """獲取教程列表"""
        tutorials = []
        for tutorial_id, tutorial in self.tutorials.items():
            tutorials.append({
                "id": tutorial_id,
                "title": tutorial["title"],
                "description": tutorial["description"],
                "difficulty": tutorial["difficulty"],
                "estimated_time": tutorial["estimated_time"],
                "prerequisites": tutorial["prerequisites"]
            })
        return tutorials

    def get_user_progress(self, user_id: str = "default_user") -> Dict[str, Any]:
        """獲取用戶學習進度"""
        progress_files = list(self.progress_dir.glob(f"{user_id}_*.json"))

        completed_tutorials = []
        total_time = 0
        total_score = 0

        for progress_file in progress_files:
            try:
                with open(progress_file, 'r', encoding='utf-8') as f:
                    progress_data = json.load(f)
                    completed_tutorials.append(progress_data["tutorial_id"])
                    total_time += progress_data.get("time_spent", 0)
                    total_score += progress_data.get("score", 0)
            except Exception as e:
                logger.warning(f"讀取進度文件失敗 {progress_file}: {e}")

        return {
            "completed_tutorials": completed_tutorials,
            "total_tutorials": len(self.tutorials),
            "completion_rate": len(completed_tutorials) / len(self.tutorials) * 100,
            "total_learning_time": total_time,
            "average_score": total_score / len(completed_tutorials) if completed_tutorials else 0
        }

if __name__ == "__main__":
    # 簡單測試
    tutorial = InteractiveTutorial()

    # 顯示教程列表
    print("可用教程：")
    for t in tutorial.get_tutorial_list():
        print(f"• {t['title']} ({t['difficulty']}, {t['estimated_time']}分鐘)")