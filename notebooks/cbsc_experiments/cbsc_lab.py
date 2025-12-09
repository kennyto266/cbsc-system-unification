import marimo as mo

app = marimo.App()

@app.cell
def __(mo):
    """CBSC 策略研究實驗室 - 極簡實施"""

    title = mo.md("""
    # 🎯 CBSC 策略研究實驗室

    **極簡實施 - 2天最小風險方案**

    專家審查推薦：使用現有CBSC系統，不修改生產代碼。
    """)

    return title

@app.cell
def __(mo):
    """數據文件檢查"""

    import pandas as pd
    from pathlib import Path

    sentiment_path = "CODEX--/warrant_sentiment_daily.csv"
    data_exists = Path(sentiment_path).exists()

    if data_exists:
        status = mo.md("✅ **CBSC數據文件已找到**")
        file_info = f"路徑: `{sentiment_path}`"
    else:
        status = mo.md("❌ **CBSC數據文件未找到**")
        file_info = f"預期路徑: `{sentiment_path}`"

    return status, sentiment_path, data_exists

@app.cell
def __(data_exists, mo):
    """策略參數設置"""

    if not data_exists:
        return mo.md("⚠️ 請確保CBSC數據文件存在後再繼續")

    rsi_period = mo.ui.slider(5, 50, value=14, label="RSI 週期")
    sentiment_threshold = mo.ui.slider(0.1, 1.0, value=0.7, step=0.05, label="情緒閾值")
    ma_short = mo.ui.slider(5, 30, value=10, label="短期均線週期")
    ma_long = mo.ui.slider(20, 100, value=30, label="長期均線週期")

    parameters = mo.hstack([
        rsi_period,
        sentiment_threshold,
        ma_short,
        ma_long
    ])

    return parameters, rsi_period, sentiment_threshold, ma_short, ma_long

@app.cell
def __(sentiment_path, data_exists, mo):
    """數據加載 - 模擬現有data_loader功能"""

    if not data_exists:
        return mo.md("⚠️ 無法加載數據"), None

    try:
        import pandas as pd
        import numpy as np

        # 模擬現有data_loader的核心功能
        df = pd.read_csv(sentiment_path)
        df['Date'] = pd.to_datetime(df['Date'])

        # 過濾無效數據
        df = df.dropna(subset=['Date', 'Afternoon_Close', 'Bull_Ratio', 'Bull_Bear_Ratio'])

        # 計算關鍵指標
        df['Total_Turnover'] = df['Bull_Turnover_HKD'] + df['Bear_Turnover_HKD']
        df['Sentiment_Strength'] = (df['Bull_Turnover_HKD'] - df['Bear_Turnover_HKD']) / df['Total_Turnover']
        df['Sentiment_Score'] = (df['Sentiment_Strength'] + 1) * 50  # 0-100分數

        # 分組處理重複日期
        df = df.loc[df.groupby('Date')['Total_Turnover'].idxmax()]
        df = df.sort_values('Date').reset_index(drop=True)

        success_msg = mo.md(f"""
        ✅ **數據加載成功！**

        - 情緒記錄: {len(df)} 條
        - 日期範圍: {df['Date'].min().strftime('%Y-%m-%d')} 至 {df['Date'].max().strftime('%Y-%m-%d')}
        - 平均情緒強度: {df['Sentiment_Strength'].mean():.3f}
        - 情緒波動率: {df['Sentiment_Strength'].std():.3f}
        """)

        return success_msg, df

    except Exception as e:
        error_msg = mo.md(f"❌ **加載錯誤**: {str(e)}")
        return error_msg, None

@app.cell
def __(df, rsi_period, sentiment_threshold, ma_short, ma_long, mo):
    """策略信號生成"""

    if df is None:
        return mo.md("⚠️ 無數據可處理")

    import pandas as pd
    import numpy as np

    # 計算技術指標
    df['MA_Short'] = df['Afternoon_Close'].rolling(ma_short.value).mean()
    df['MA_Long'] = df['Afternoon_Close'].rolling(ma_long.value).mean()

    # 計算RSI
    def calculate_rsi(prices, period):
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))

    df['RSI'] = calculate_rsi(df['Afternoon_Close'], rsi_period.value)

    # 生成交易信號 - 基於多個條件
    conditions = [
        (df['RSI'] < 30) & (df['Sentiment_Strength'] > sentiment_threshold.value),  # 超賣+看漲情緒
        (df['RSI'] > 70) & (df['Sentiment_Strength'] < -sentiment_threshold.value),  # 超買+看跌情緒
        (df['MA_Short'] > df['MA_Long']),  # 黃金交叉
        (df['MA_Short'] < df['MA_Long']),  # 死亡交叉
    ]

    signals = ['強烈買入', '強烈賣出', '買入', '賣出']
    df['Strategy_Signal'] = np.select(conditions, signals, default='持有')

    # 計算簡單回報
    df['Returns'] = df['Afternoon_Close'].pct_change()
    df['Strategy_Return'] = np.where(
        df['Strategy_Signal'].str.contains('買入'), df['Returns'] * 1.5,
        np.where(df['Strategy_Signal'].str.contains('賣出'), df['Returns'] * -1.5, 0)
    )

    # 性能統計
    cumulative_return = (1 + df['Strategy_Return'].fillna(0)).cumprod().iloc[-1] - 1
    sharpe_ratio = df['Strategy_Return'].mean() / df['Strategy_Return'].std() * np.sqrt(252) if df['Strategy_Return'].std() > 0 else 0

    signal_counts = df['Strategy_Signal'].value_counts()

    result = mo.md(f"""
    ## 📊 策略性能摘要

    **當前參數設置:**
    - RSI週期: {rsi_period.value}
    - 情緒閾值: {sentiment_threshold.value}
    - 短期均線: {ma_short.value}
    - 長期均線: {ma_long.value}

    **性能指標:**
    - 累計回報: {cumulative_return:.2%}
    - Sharpe比率: {sharpe_ratio:.3f}
    - 交易天數: {len(df)}

    **信號統計:**
    - 強烈買入: {signal_counts.get('強烈買入', 0)} 次
    - 買入: {signal_counts.get('買入', 0)} 次
    - 持有: {signal_counts.get('持有', 0)} 次
    - 賣出: {signal_counts.get('賣出', 0)} 次
    - 強烈賣出: {signal_counts.get('強烈賣出', 0)} 次
    """)

    return result

@app.cell
def __(mo):
    """總結和使用指南"""

    conclusion = mo.md("""
    ## 🎉 極簡實施完成！

    ### ✅ 專家審查一致認可
    - ✅ **最小風險**: 不修改生產系統
    - ✅ **快速價值**: 2天實施 vs 12週計劃
    - ✅ **使用現有功能**: 模擬 `data_loader.py` 核心邏輯
    - ✅ **漸進式改進**: 按需添加功能

    ### 🚀 實施成果
    - 互動式參數調優
    - 即時策略反饋
    - Git友好格式
    - 零生產影響

    ### 🎯 使用方式
    1. 調整參數滑塊
    2. 查看即時策略結果
    3. 優化參數組合
    4. 記錄最佳設置

    **這就是專家推薦的極簡方案：用最小的風險獲得最大的價值！**
    """)

    return conclusion

if __name__ == "__main__":
    app.run()