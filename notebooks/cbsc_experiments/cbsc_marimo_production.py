# Copyright 2024 Marimo. All rights reserved.

import marimo

__generated_with = "0.18.2"
app = marimo.App(width="medium")


@app.cell
def _():
    return


@app.cell
def _():
    return


@app.cell
def _():
    # 核心模塊導入 - 單一導入點
    import marimo as mo
    import pandas as pd
    import numpy as np
    from pathlib import Path
    import os
    return Path, mo, np, pd


@app.cell
def _(mo):
    # 界面標題和介紹
    title = mo.md("# 🚀 CBSC 智能量化實驗室")
    intro = mo.md("""
    **基於 Marimo 的專業量化交易研究平台**

    ✅ 實時數據分析
    ✅ 交互式參數調優
    ✅ 策略性能監控
    ✅ AI 增強功能
    """)
    return


@app.cell
def _(Path, mo, pd):
    # 數據加載和驗證
    current_dir = Path.cwd()
    sentiment_path = current_dir / "warrant_sentiment_daily.csv"
    data_exists = sentiment_path.exists()

    if data_exists:
        try:
            # 安全加載數據
            df = pd.read_csv(sentiment_path)
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
            df = df.dropna(subset=['Date', 'Afternoon_Close'])
            df = df.sort_values('Date').reset_index(drop=True)

            data_status = mo.md(f"""
            ✅ **CBSC 數據加載成功**

            - 記錄數量: {len(df)} 條
            - 日期範圍: {df['Date'].min().strftime('%Y-%m-%d')} 至 {df['Date'].max().strftime('%Y-%m-%d')}
            - 數據完整性: ✅
            """)

        except Exception as e:
            data_status = mo.md(f"❌ **數據加載失敗**: {str(e)}")
            df = pd.DataFrame()
    else:
        data_status = mo.md(f"❌ **數據文件未找到**: `{sentiment_path}`")
        df = pd.DataFrame()
    return (df,)


@app.cell
def _(mo):
    # 交互式參數控制
    rsi_period = mo.ui.slider(5, 50, value=14, label="RSI 週期")
    sentiment_threshold = mo.ui.slider(0.1, 1.0, value=0.7, step=0.05, label="情緒閾值")
    ma_short = mo.ui.slider(5, 30, value=10, label="短期均線")
    ma_long = mo.ui.slider(20, 100, value=30, label="長期均線")

    # 分析開關
    enable_analysis = mo.ui.switch(label="啟用詳細分析", value=True)
    return enable_analysis, ma_long, ma_short, rsi_period, sentiment_threshold


@app.cell
def _(df, ma_long, ma_short, mo, np, rsi_period, sentiment_threshold):
    # 策略計算和技術指標

    if df.empty:
        strategy_result = mo.md("⚠️ **無數據可進行策略計算**")
        analysis_df = df.copy()
    else:
        try:
            # 複製數據避免修改原始數據
            analysis_df = df.copy()

            # 情緒強度計算
            analysis_df['Total_Turnover'] = (
                analysis_df.get('Bull_Turnover_HKD', 0) +
                analysis_df.get('Bear_Turnover_HKD', 0)
            )
            analysis_df['Sentiment_Strength'] = (
                (analysis_df.get('Bull_Turnover_HKD', 0) -
                 analysis_df.get('Bear_Turnover_HKD', 0)) /
                analysis_df['Total_Turnover'].replace(0, 1)
            )

            # 技術指標計算
            analysis_df['MA_Short'] = analysis_df['Afternoon_Close'].rolling(ma_short.value).mean()
            analysis_df['MA_Long'] = analysis_df['Afternoon_Close'].rolling(ma_long.value).mean()

            # RSI 計算
            delta = analysis_df['Afternoon_Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=rsi_period.value).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_period.value).mean()
            rs = gain / loss.where(loss != 0, 1)
            analysis_df['RSI'] = 100 - (100 / (1 + rs))

            # 簡化策略信號
            analysis_df['Signal'] = np.where(
                (analysis_df['RSI'] < 30) & (analysis_df['Sentiment_Strength'] > sentiment_threshold.value),
                "買入",
                np.where((analysis_df['RSI'] > 70) & (analysis_df['Sentiment_Strength'] < -sentiment_threshold.value),
                         "賣出", "持有")
            )

            # 統計信息
            signal_counts = analysis_df['Signal'].value_counts()
            latest_signal = analysis_df['Signal'].iloc[-1]
            latest_rsi = analysis_df['RSI'].iloc[-1]
            latest_sentiment = analysis_df['Sentiment_Strength'].iloc[-1]

            strategy_result = mo.md(f"""
            🎯 **策略分析結果**

            **最新市場狀態**:
            - 當前信號: {latest_signal}
            - RSI 指標: {latest_rsi:.1f}
            - 情緒強度: {latest_sentiment:.3f}

            **信號分佈**:
            - 買入: {signal_counts.get('買入', 0)} 次
            - 持有: {signal_counts.get('持有', 0)} 次
            - 賣出: {signal_counts.get('賣出', 0)} 次

            **參數設置**:
            - RSI 週期: {rsi_period.value}
            - 情緒閾值: {sentiment_threshold.value:.2f}
            - 短期均線: {ma_short.value}
            - 長期均線: {ma_long.value}
            """)

        except Exception as e:
            strategy_result = mo.md(f"❌ **策略計算錯誤**: {str(e)}")
            analysis_df = df.copy()
    return (analysis_df,)


@app.cell
def _(analysis_df, enable_analysis, mo, np):
    # 詳細分析和洞察

    if analysis_df.empty or not enable_analysis.value:
        insights = mo.md("📊 **詳細分析已禁用**")
    else:
        try:
            # 計算性能指標
            returns = analysis_df['Afternoon_Close'].pct_change().dropna()

            if len(returns) > 0:
                volatility = returns.std() * np.sqrt(252) * 100
                max_drawdown = ((analysis_df['Afternoon_Close'].expanding().max() -
                               analysis_df['Afternoon_Close']) /
                              analysis_df['Afternoon_Close'].expanding().max()).max() * 100

                insights = mo.accordion({
                    "📈 詳細性能分析": f"""
                    **風險指標**:
                    - 年化波動率: {volatility:.2f}%
                    - 最大回撤: {max_drawdown:.2f}%

                    **市場趨勢**:
                    - 平均日回報: {returns.mean()*100:.3f}%
                    - 正回報天數: {len(returns[returns > 0])} 天
                    - 負回報天數: {len(returns[returns < 0])} 天
                    """
                })
            else:
                insights = mo.md("⚠️ **無足夠數據進行詳細分析**")

        except Exception as e:
            insights = mo.md(f"❌ **詳細分析錯誤**: {str(e)}")
    return


@app.cell
def _(mo):
    # 使用指南
    guide = mo.accordion({
        "📖 使用指南": """
        **🎯 快速開始**:
        1. 確保 CBSC 數據文件存在
        2. 調整參數滑塊
        3. 查看即時策略結果
        4. 啟用詳細分析獲得更多洞察

        **📊 數據要求**:
        - 文件名: `warrant_sentiment_daily.csv`
        - 必需欄位: Date, Afternoon_Close, Bull_Turnover_HKD, Bear_Turnover_HKD

        **⚙️ 參數說明**:
        - **RSI 週期**: 技術指標計算週期 (5-50)
        - **情緒閾值**: 情緒強度判斷閾值 (0.1-1.0)
        - **均線週期**: 移動平均線計算週期
        """
    })
    return


if __name__ == "__main__":
    app.run()
