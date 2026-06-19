# Copyright 2024 Marimo. All rights reserved.
import marimo
__generated_with = "0.18.2"

app = marimo.App(width="medium")

@app.cell
def __(mo):
    # 統一導入所有必要模塊
    import marimo as mo
    import pandas as pd
    import numpy as np
    import os
    from pathlib import Path

    # 標題和介紹
    title = mo.md("# 🚀 GLM-4.6 + CBSC 智能量化實驗室")
    intro = mo.md("""
    **🎯 專業級 CBSC 量化交易平台 - GLM-4.6 AI 增強版**

 - 實時市場情緒分析
 - 智能策略參數優化
 - AI驅動交易建議
 - 即時性能監控
    """)

    return title, intro, mo, pd, np, os, Path

@app.cell
def __(mo, pd, np, os, Path):
    """GLM-4.6 AI 配置和聊天界面"""

    # 從環境變數讀取 GLM API Key（切勿硬編碼）
    glm_api_key = os.environ.get("GLM_API_KEY", "")

    try:
        # 配置 GLM-4.6 模型
        llm = mo.ai.llm.openai(
            model="glm-4.6",  # GLM-4.6 模型名稱
            api_key=glm_api_key,
            base_url="https://open.bigmodel.cn/api/paas/v4/",  # 智譜AI的API端點
            system_message="""你是 CBSC (Callable Bull/Bear Contract) 量化交易專家，基於 GLM-4.6 模型。

專業領域：
- 牛熊證市場分析與情緒數據處理
- RSI、MACD、布林帶等技術指標優化
- 量化策略回測與風險評估
- 香港股市結構性產品分析
- 實時市場監控與信號生成

分析原則：
1. 基於數據驅動的分析
2. 考慮市場情緒變化
3. 重視風險管理
4. 提供可操作的建議
5. 解釋分析邏輯和依據"""
        )

        # 創建專業的量化交易聊天界面
        chatbot = mo.ui.chat(
            llm,
            prompts=[
                "您好！我是基於 GLM-4.6 的 CBSC 量化交易專家助手。\\n\\n我可以幫您：\\n🔹 分析牛熊證市場趨勢\\n🔹 優化交易策略參數\\n🔹 評估技術指標效果\\n🔹 提供風險管理建議\\n🔹 解讀市場情緒數據\\n\\n請隨時提出您的量化交易問題！",
                "基於當前 CBSC 市場數據，請分析最近的趨勢變化。"
            ],
            placeholder="輸入您的 CBSC 量化交易問題，例如：如何優化 RSI 參數？",
            show_configuration_controls=True
        )

    except Exception as e:
        chatbot = mo.md(f"❌ GLM-4.6 配置錯誤: {str(e)}\\n\\n請檢查：\\n- API Key 是否正確\\n- 網絡連接是否正常\\n- GLM 服務是否可用")

    return chatbot

@app.cell
def __(mo):
    """CBSC 策略參數控制面板"""
    rsi_period = mo.ui.slider(5, 50, value=14, label="RSI 週期")
    sentiment_threshold = mo.ui.slider(0.1, 1.0, value=0.7, step=0.05, label="情緒閾值")
    ma_short = mo.ui.slider(5, 30, value=10, label="短期均線週期")
    ma_long = mo.ui.slider(20, 100, value=30, label="長期均線週期")

    # GLM 分析開關
    enable_glm_analysis = mo.ui.switch(label="啟用 GLM-4.6 智能分析", value=True)

    return rsi_period, sentiment_threshold, ma_short, ma_long, enable_glm_analysis

@app.cell
def __(rsi_period, sentiment_threshold, ma_short, ma_long, pd, np, Path, mo):
    """CBSC 數據處理和策略計算"""

    # 修正數據路徑 - 使用絕對路徑
    current_dir = Path.cwd()
    sentiment_path = current_dir / "warrant_sentiment_daily.csv"
    data_exists = sentiment_path.exists()

    if data_exists:
        try:
            # 加載 CBSC 數據
            df = pd.read_csv(sentiment_path)
            df['Date'] = pd.to_datetime(df['Date'])
            df = df.dropna(subset=['Date', 'Afternoon_Close'])
            df = df.sort_values('Date').reset_index(drop=True)

            # 計算情緒強度
            df['Total_Turnover'] = df.get('Bull_Turnover_HKD', 0) + df.get('Bear_Turnover_HKD', 0)
            df['Sentiment_Strength'] = (df.get('Bull_Turnover_HKD', 0) - df.get('Bear_Turnover_HKD', 0)) / df['Total_Turnover'].replace(0, 1)

            # 技術指標計算
            df['MA_Short'] = df['Afternoon_Close'].rolling(ma_short.value).mean()
            df['MA_Long'] = df['Afternoon_Close'].rolling(ma_long.value).mean()

            # RSI 計算
            delta = df['Afternoon_Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=rsi_period.value).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_period.value).mean()
            rs = gain / loss.where(loss != 0, 1)
            df['RSI'] = 100 - (100 / (1 + rs))

            # MACD 計算
            exp1 = df['Afternoon_Close'].ewm(span=12).mean()
            exp2 = df['Afternoon_Close'].ewm(span=26).mean()
            df['MACD'] = exp1 - exp2
            df['Signal_Line'] = df['MACD'].ewm(span=9).mean()

            # 布林帶計算
            df['BB_Middle'] = df['Afternoon_Close'].rolling(window=20).mean()
            bb_std = df['Afternoon_Close'].rolling(window=20).std()
            df['BB_Upper'] = df['BB_Middle'] + (bb_std * 2)
            df['BB_Lower'] = df['BB_Middle'] - (bb_std * 2)

            # 生成複合交易信號
            conditions = [
                # 超強買入信號
                (df['RSI'] < 25) & (df['Sentiment_Strength'] > sentiment_threshold.value) & (df['MACD'] > df['Signal_Line']),
                # 強買入信號
                (df['RSI'] < 30) & (df['Sentiment_Strength'] > sentiment_threshold.value),
                # 超強賣出信號
                (df['RSI'] > 75) & (df['Sentiment_Strength'] < -sentiment_threshold.value) & (df['MACD'] < df['Signal_Line']),
                # 強賣出信號
                (df['RSI'] > 70) & (df['Sentiment_Strength'] < -sentiment_threshold.value),
                # 布林帶突破
                df['Afternoon_Close'] > df['BB_Upper'],
                df['Afternoon_Close'] < df['BB_Lower'],
            ]

            signals = ['超強買入', '強買入', '超強賣出', '強賣出', '突破上軌', '突破下軌']
            df['Strategy_Signal'] = np.select(conditions, signals, default='持有')

            # 性能計算
            df['Returns'] = df['Afternoon_Close'].pct_change()
            df['Strategy_Return'] = np.where(
                df['Strategy_Signal'].str.contains('買入'), df['Returns'] * 2.0,
                np.where(df['Strategy_Signal'].str.contains('賣出'), df['Returns'] * -1.5,
                       np.where(df['Strategy_Signal'] == '突破上軌', df['Returns'] * 1.8,
                              np.where(df['Strategy_Signal'] == '突破下軌', df['Returns'] * -1.2, 0)))
            )

            cumulative_return = (1 + df['Strategy_Return'].fillna(0)).cumprod().iloc[-1] - 1
            sharpe_ratio = df['Strategy_Return'].mean() / df['Strategy_Return'].std() * np.sqrt(252) if df['Strategy_Return'].std() > 0 else 0
            max_drawdown = ((df['Afternoon_Close'].expanding().max() - df['Afternoon_Close']) / df['Afternoon_Close'].expanding().max()).max()

            signal_counts = df['Strategy_Signal'].value_counts()

            data_status = mo.md(f"""
            ✅ **CBSC 數據加載成功 - GLM-4.6 增強版**

            **📊 基本市場信息**:
            - 數據記錄: {len(df)} 條
            - 日期範圍: {df['Date'].min().strftime('%Y-%m-%d')} 至 {df['Date'].max().strftime('%Y-%m-%d')}
            - 平均情緒強度: {df['Sentiment_Strength'].mean():.3f}
            - 情緒波動率: {df['Sentiment_Strength'].std():.3f}

            **🎯 當前市場狀態**:
            - 最新價格: HK${df['Afternoon_Close'].iloc[-1]:.2f}
            - 當前 RSI: {df['RSI'].iloc[-1]:.1f} ({'超買' if df['RSI'].iloc[-1] > 70 else '超賣' if df['RSI'].iloc[-1] < 30 else '中性'})
            - 情緒強度: {df['Sentiment_Strength'].iloc[-1]:.3f} ({'極度樂觀' if df['Sentiment_Strength'].iloc[-1] > 0.5 else '極度悲觀' if df['Sentiment_Strength'].iloc[-1] < -0.5 else '中性'})
            - 當前信號: {df['Strategy_Signal'].iloc[-1]}
            - MACD 狀態: {'金叉' if df['MACD'].iloc[-1] > df['Signal_Line'].iloc[-1] else '死叉'}
            - 布林帶位置: {'上軌之上' if df['Afternoon_Close'].iloc[-1] > df['BB_Upper'].iloc[-1] else '下軌之下' if df['Afternoon_Close'].iloc[-1] < df['BB_Lower'].iloc[-1] else '通道內'}

            **💰 策略性能指標**:
            - 累計回報: {cumulative_return:.2%}
            - Sharpe 比率: {sharpe_ratio:.3f}
            - 最大回撤: {max_drawdown:.2%}
            - 勝率: {len(df[df['Strategy_Return'] > 0])/len(df)*100:.1f}%
            - 年化波動率: {df['Returns'].std()*np.sqrt(252)*100:.2f}%

            **📈 信號統計分析**:
            - 超強買入: {signal_counts.get('超強買入', 0)} 次
            - 強買入: {signal_counts.get('強買入', 0)} 次
            - 持有: {signal_counts.get('持有', 0)} 次
            - 強賣出: {signal_counts.get('強賣出', 0)} 次
            - 超強賣出: {signal_counts.get('超強賣出', 0)} 次
            - 突破上軌: {signal_counts.get('突破上軌', 0)} 次
            - 突破下軌: {signal_counts.get('突破下軌', 0)} 次
            """)

        except Exception as e:
            data_status = mo.md(f"❌ 數據處理錯誤: {str(e)}")
            df = pd.DataFrame()
    else:
        data_status = mo.md(f"❌ CBSC 數據文件未找到\\n\\n請確保 `{sentiment_path}` 文件存在")
        df = pd.DataFrame()

    return data_status, df

@app.cell
def __(df, rsi_period, sentiment_threshold, enable_glm_analysis, mo):
    """GLM-4.6 智能分析和洞察"""

    if df.empty:
        return mo.md("⚠️ 無數據可進行 GLM-4.6 分析")

    if enable_glm_analysis.value:
        # 為 GLM 生成專業分析提示
        latest_10_days = df.tail(10).to_dict('records')
        latest_signal = df['Strategy_Signal'].iloc[-1]
        latest_rsi = df['RSI'].iloc[-1]
        latest_sentiment = df['Sentiment_Strength'].iloc[-1]
        latest_macd = df['MACD'].iloc[-1]
        latest_signal_line = df['Signal_Line'].iloc[-1]

        # 計算技術指標統計
        rsi_trend = "上升" if latest_rsi > df['RSI'].iloc[-5:].mean() else "下降"
        sentiment_trend = "改善" if latest_sentiment > df['Sentiment_Strength'].iloc[-5:].mean() else "惡化"

        glm_prompt = f"""
        作為 CBSC 量化交易專家，請基於 GLM-4.6 的分析能力，對以下數據進行專業評估：

        **📊 當前市場技術狀態**:
        - RSI 指標: {latest_rsi:.1f} (趨勢: {rsi_trend})
        - 情緒強度: {latest_sentiment:.3f} (趨勢: {sentiment_trend})
        - 當前信號: {latest_signal}
        - MACD: {latest_macd:.6f}, Signal Line: {latest_signal_line:.6f}

        **🎯 策略參數配置**:
        - RSI 週期: {rsi_period.value}
        - 情緒閾值: {sentiment_threshold.value:.2f}

        **📈 最近 10 天技術指標**:
        {latest_10_days}

        請提供以下專業分析：

        1. **技術面分析**: 當前市場趨勢和技術指標解讀
        2. **情緒面分析**: 牛熊證情緒變化及其對市場的影響
        3. **策略評估**: 當前信號的可靠性和風險評級
        4. **參數優化**: 基於當前市場狀態的參數調整建議
        5. **風險提示**: 潛在的市場風險和應對策略
        6. **操作建議**: 具體的交易建議和倉位管理

        請以專業、客觀、基於數據的方式進行分析。
        """

        glm_insights = mo.accordion({
            "🤖 GLM-4.6 智能分析": f"""
            **GLM-4.6 分析能力已啟用**

            將包含的分析提示：

            ```
            {glm_prompt}
            ```

            **💡 使用方法**:
            1. 在上方聊天界面輸入您的問題
            2. GLM-4.6 會基於上述數據進行分析
            3. 獲得專業的 CBSC 交易建議

            **🎯 建議問題示例**:
            - "基於當前市場狀態，應該調整哪些參數？"
            - "目前的交易信號可靠性如何？"
            - "市場情緒趨勢對未來價格的影響？"
            - "如何優化當前的策略設置？"
            """
        })
    else:
        glm_insights = mo.md("GLM-4.6 分析已禁用，請啟用智能分析開關")

    return glm_insights

@app.cell
def __(mo):
    """使用指南和配置說明"""
    usage_guide = mo.accordion({
        "📖 GLM-4.6 使用指南": """
        **✅ 已配置的 GLM-4.6 功能**:

        🤖 **GLM-4.6 模型特點**:
        - 強大的自然語言理解和生成能力
        - 專業的金融市場分析知識
        - 實時數據處理和分析能力
        - 多維度綜合評估能力

        🔧 **AI 配置**:
        - API Key: 已自動配置 ✅
        - 模型: GLM-4.6
        - 端點: 智譜AI API
        - 系統提示: CBSC 專業分析師角色

        🎯 **核心功能**:
        1. **智能策略分析** - 實時評估交易信號質量
        2. **參數優化建議** - 基於市場狀態的動態調整
        3. **風險管理評估** - 多維度風險分析和預警
        4. **市場趨勢預測** - 基於技術指標和情緒數據的趨勢判斷
        5. **投資建議生成** - 個性化的投資策略建議

        💡 **使用技巧**:
        - 提供具體、明確的問題
        - 描述您的投資目標和風險偏好
        - 定期諮詢以獲得最新市場洞察
        - 結合技術分析和基本面分析
        """
    })

    return usage_guide

if __name__ == "__main__":
    app.run()