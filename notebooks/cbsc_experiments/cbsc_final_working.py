import marimo as mo

app = marimo.App(width="medium")

@app.cell
def __(mo):
    return mo.md("# 🎯 CBSC 策略實驗室")

@app.cell
def __(mo):
    rsi_period = mo.ui.slider(5, 50, value=14, label="RSI 週期")
    sentiment_threshold = mo.ui.slider(0.1, 1.0, value=0.7, label="情緒閾值")
    return rsi_period, sentiment_threshold

@app.cell
def __(rsi_period, sentiment_threshold):
    import pandas as pd

    # 檢查數據文件
    try:
        df = pd.read_csv("CODEX--/warrant_sentiment_daily.csv")
        data_loaded = True
        records = len(df)
    except:
        data_loaded = False
        records = 0

    return mo.md(f"""
    數據狀態: {"✅ 已加載" if data_loaded else "❌ 未找到"}
    記錄數量: {records}
    RSI設置: {rsi_period.value}
    情緒閾值: {sentiment_threshold.value}
    """)

if __name__ == "__main__":
    app.run()