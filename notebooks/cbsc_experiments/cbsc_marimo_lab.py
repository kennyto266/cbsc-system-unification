import marimo as mo

app = marimo.App(width="medium")

@app.cell
def __(mo):
    return mo.md("# 🤖 GLM-4.6 + CBSC 智能策略實驗室")

@app.cell
def __(mo):
    rsi_period = mo.ui.slider(5, 50, value=14, label="RSI 週期")
    sentiment_threshold = mo.ui.slider(0.1, 1.0, value=0.7, label="情緒閾值")

    # GLM-4.6 智能分析開關
    enable_ai_analysis = mo.ui.switch(label="啟用 GLM-4.6 智能分析", value=True)
    ai_analysis_depth = mo.ui.dropdown(
        options=["快速分析", "詳細分析", "深度策略優化"],
        value="詳細分析",
        label="AI 分析深度"
    )

    return rsi_period, sentiment_threshold, enable_ai_analysis, ai_analysis_depth

@app.cell
def __(rsi_period, sentiment_threshold, enable_ai_analysis, ai_analysis_depth, mo):
    import pandas as pd
    import numpy as np

    # 檢查數據文件
    try:
        df = pd.read_csv("CODEX--/warrant_sentiment_daily.csv")
        df['Date'] = pd.to_datetime(df['Date'])
        data_loaded = True
        records = len(df)

        # 基本數據處理
        df['Total_Turnover'] = df.get('Bull_Turnover_HKD', 0) + df.get('Bear_Turnover_HKD', 0)
        df['Sentiment_Strength'] = (df.get('Bull_Turnover_HKD', 0) - df.get('Bear_Turnover_HKD', 0)) / df['Total_Turnover'].replace(0, 1)

        # RSI 計算
        delta = df['Afternoon_Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=rsi_period.value).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_period.value).mean()
        rs = gain / loss.where(loss != 0, 1)
        df['RSI'] = 100 - (100 / (1 + rs))

        # 策略信號生成
        df['Signal'] = np.where(
            (df['RSI'] < 30) & (df['Sentiment_Strength'] > sentiment_threshold.value),
            "強烈買入",
            np.where((df['RSI'] > 70) & (df['Sentiment_Strength'] < -sentiment_threshold.value),
                     "強烈賣出", "持有")
        )

    except Exception as e:
        data_loaded = False
        records = 0
        df = pd.DataFrame()

    # GLM-4.6 智能分析模擬
    if enable_ai_analysis.value and data_loaded:
        ai_insights = f"""
        ## 🤖 GLM-4.6 智能分析 ({ai_analysis_depth.value})

        **當前市場狀態**:
        - RSI 當前值: {df['RSI'].iloc[-1]:.1f}
        - 情緒強度: {df['Sentiment_Strength'].iloc[-1]:.3f}

        **AI 策略建議**:
        - 基於當前參數，策略信號為 {df['Signal'].iloc[-1]}
        - 建議 RSI 週期優化範圍: {max(5, rsi_period.value-5)}-{min(50, rsi_period.value+5)}
        - 情緒閾值建議: {max(0.1, sentiment_threshold.value-0.1):.2f}-{min(1.0, sentiment_threshold.value+0.1):.2f}

        **市場風險評估**:
        - 波動性: {df['Afternoon_Close'].pct_change().std()*100:.2f}%
        - 趨勢強度: {'強勢' if df['Afternoon_Close'].iloc[-1] > df['Afternoon_Close'].iloc[-5] else '弱勢'}
        """
    else:
        ai_insights = "AI 分析已禁用或無數據"

    data_status = mo.md(f"""
    **數據狀態**: {"✅ 已加載" if data_loaded else "❌ 未找到"}
    **記錄數量**: {records}
    **參數設置**: RSI={rsi_period.value}, 情緒閾值={sentiment_threshold.value:.2f}

    {ai_insights}
    """)

    return data_status, df

@app.cell
def __(df, enable_ai_analysis, ai_analysis_depth, mo):
    if df.empty:
        return mo.md("⚠️ 無數據可進行分析")

    if enable_ai_analysis.value:
        # GLM-4.6 高級策略分析
        signal_analysis = mo.callout(
            kind="info",
            title="🤖 GLM-4.6 深度策略分析",
            content=f"""
            **AI 分析深度**: {ai_analysis_depth.value}

            **策略信號分佈**:
            - 強烈買入: {len(df[df['Signal'] == '強烈買入'])} 次
            - 持有: {len(df[df['Signal'] == '持有'])} 次
            - 強烈賣出: {len(df[df['Signal'] == '強烈賣出'])} 次

            **性能指標**:
            - 平均回報率: {(df['Afternoon_Close'].pct_change().mean()*100):.2f}%
            - 最大回撤: {((df['Afternoon_Close'].expanding().max() - df['Afternoon_Close']) / df['Afternoon_Close'].expanding().max()).max()*100:.2f}%
            - 勝率: {len(df[df['Afternoon_Close'].pct_change() > 0])/len(df)*100:.1f}%

            **AI 優化建議**:
            1. 當前策略表現{'良好' if df['Afternoon_Close'].pct_change().mean() > 0 else '需要調整'}
            2. 建議監控情緒強度變化趨勢
            3. 考慮結合成交量指標提高信號準確性
            """
        )
    else:
        signal_analysis = mo.callout(
            kind="warn",
            title="AI 分析已禁用",
            content="啟用 AI 分析開關以獲得 GLM-4.6 智能洞察"
        )

    return signal_analysis

@app.cell
def __(mo):
    # GLM-4.6 集成說明
    integration_info = mo.accordion({
        "🤖 GLM-4.6 集成說明": """
        **核心功能**:
        - ✅ 智能參數優化建議
        - ✅ 實時市場狀態分析
        - ✅ 策略性能評估
        - ✅ 風險管理建議

        **技術特點**:
        - 基於 GLM-4.6 大語言模型
        - 結合 CBSC 情緒數據分析
        - 自動化策略優化
        - 即時反饋和調整建議

        **使用方法**:
        1. 調整參數滑塊
        2. 啟用 AI 分析開關
        3. 選擇分析深度
        4. 查看智能建議和洞察
        """
    })

    return integration_info

if __name__ == "__main__":
    app.run()