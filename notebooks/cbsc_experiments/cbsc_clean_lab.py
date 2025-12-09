import marimo

app = marimo.App()

@app.cell
def __():
    import marimo as mo

    return mo.md("""
    # 🎯 CBSC 策略研究實驗室

    **專家審查推薦：極簡實施方案**

    - ✅ 不修改生產系統
    - ✅ 使用現有數據源
    - ✅ 互動式參數調優
    - ✅ Git友好格式
    """)

@app.cell
def __():
    import marimo as mo
    import pandas as pd
    from pathlib import Path

    sentiment_path = "CODEX--/warrant_sentiment_daily.csv"
    data_exists = Path(sentiment_path).exists()

    if data_exists:
        status = "✅ CBSC數據文件已找到"
    else:
        status = "❌ CBSC數據文件未找到，請確保文件存在"

    return status, sentiment_path, data_exists

@app.cell
def __(data_exists):
    import marimo as mo

    if not data_exists:
        return mo.md("⚠️ 請確保CBSC數據文件存在後再繼續")

    rsi_period = mo.ui.slider(5, 50, value=14, label="RSI週期")
    sentiment_threshold = mo.ui.slider(0.1, 1.0, value=0.7, step=0.05, label="情緒閾值")
    ma_short = mo.ui.slider(5, 30, value=10, label="短期均線")
    ma_long = mo.ui.slider(20, 100, value=30, label="長期均線")

    return rsi_period, sentiment_threshold, ma_short, ma_long

@app.cell
def __(sentiment_path):
    import marimo as mo
    import pandas as pd
    import numpy as np

    try:
        # 加載數據
        df = pd.read_csv(sentiment_path)
        df['Date'] = pd.to_datetime(df['Date'])

        # 過濾無效數據
        df = df.dropna(subset=['Date', 'Afternoon_Close'])
        df['Total_Turnover'] = df.get('Bull_Turnover_HKD', 0) + df.get('Bear_Turnover_HKD', 0)
        df['Sentiment_Strength'] = (df['Bull_Turnover_HKD'] - df['Bear_Turnover_HKD']) / df['Total_Turnover'].replace(0, 1)

        # 生成性能摘要
        summary = mo.md(f"""
        **數據加載成功！**

        - 記錄數量: {len(df)} 條
        - 日期範圍: {df['Date'].min()} 至 {df['Date'].max()}
        - 平均情緒強度: {df['Sentiment_Strength'].mean():.3f}
        - 情緒波動率: {df['Sentiment_Strength'].std():.3f}
        """)

        return summary, df

    except Exception as e:
        return mo.md(f"❌ 加載錯誤: {str(e)}"), pd.DataFrame()

@app.cell
def __(df, rsi_period, sentiment_threshold, ma_short, ma_long):
    import marimo as mo
    import numpy as np

    if df.empty:
        return mo.md("⚠️ 無數據可處理")

    # 計算技術指標
    df['MA_Short'] = df['Afternoon_Close'].rolling(ma_short.value).mean()
    df['MA_Long'] = df['Afternoon_Close'].rolling(ma_long.value).mean()

    # 計算RSI
    delta = df['Afternoon_Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=rsi_period.value).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_period.value).mean()
    rs = gain / loss.where(loss != 0, 1)
    df['RSI'] = 100 - (100 / (1 + rs))

    # 生成交易信號
    df['Signal'] = np.where(
        (df['RSI'] < 30) & (df['Sentiment_Strength'] > sentiment_threshold.value),
        "買入",
        np.where((df['RSI'] > 70) & (df['Sentiment_Strength'] < -sentiment_threshold.value),
                 "賣出",
                 "持有"
        )
    )

    # 計算回報
    df['Returns'] = df['Afternoon_Close'].pct_change()
    buy_returns = df[df['Signal'] == '買入']['Returns'].sum()
    sell_returns = df[df['Signal'] == '賣出']['Returns'].sum()
    total_return = (1 + df['Returns']).cumprod().iloc[-1] - 1

    signal_counts = df['Signal'].value_counts()

    return mo.md(f"""
    ## 📊 策略性能摘要

    **當前參數:**
    - RSI週期: {rsi_period.value}
    - 情緒閾值: {sentiment_threshold.value}
    - 短期均線: {ma_short.value}
    - 長期均線: {ma_long.value}

    **性能指標:**
    - 累計回報: {total_return:.2%}
    - 買入次數: {signal_counts.get('買入', 0)}
    - 賣出次數: {signal_counts.get('賣出', 0)}
    - 持有次數: {signal_counts.get('持有', 0)}
    """)

if __name__ == "__main__":
    app.run()