import marimo as mo

app = marimo.App(width="medium")

@app.cell
def __(mo):
    title = mo.md("# 🤖 GLM-4.6 + CBSC 智能策略實驗室")
    intro = mo.md("""
    **集成了 GLM-4.6 AI 功能的 CBSC 量化交易平台**

    通過 Marimo AI 集成，提供智能策略分析、參數優化和實時市場洞察。
    """)
    return title, intro

@app.cell
def __(mo):
    import os
    from pathlib import Path

    # API 配置管理
    api_config = mo.ui.dictionary({
        "provider": mo.ui.dropdown(
            options=["openai", "anthropic", "google", "azure", "custom"],
            value="openai",
            label="AI 提供商"
        ),
        "api_key": mo.ui.text(
            value=os.environ.get("OPENAI_API_KEY", ""),
            label="API Key",
            placeholder="輸入您的 API 密鑰"
        ),
        "model": mo.ui.text(
            value="gpt-4o-mini",
            label="模型名稱",
            placeholder="例如: gpt-4o-mini, claude-3-5-sonnet-20241022"
        ),
        "base_url": mo.ui.text(
            value="",
            label="Base URL (可選)",
            placeholder="例如: https://api.openai.com/v1"
        )
    })

    return api_config

@app.cell
def __(api_config, mo):
    """AI 助手聊天界面"""
    try:
        if api_config.value["api_key"]:
            # 根據提供商配置 LLM
            if api_config.value["provider"] == "openai":
                llm = mo.ai.llm.openai(
                    model=api_config.value["model"],
                    api_key=api_config.value["api_key"],
                    base_url=api_config.value["base_url"] or None,
                    system_message="""你是 CBSC (Callable Bull/Bear Contract) 量化交易專家。

你的專業領域包括：
- 牛熊證市場分析
- 情緒數據處理
- 技術指標優化
- 量化策略設計
- 風險管理評估

請提供專業、準確的分析建議。"""
                )
            elif api_config.value["provider"] == "anthropic":
                llm = mo.ai.llm.anthropic(
                    model=api_config.value["model"],
                    api_key=api_config.value["api_key"],
                    system_message="你是 CBSC 量化交易專家，專注於牛熊證市場分析。"
                )
            elif api_config.value["provider"] == "custom":
                llm = mo.ai.llm.openai(
                    model=api_config.value["model"],
                    api_key=api_config.value["api_key"],
                    base_url=api_config.value["base_url"],
                    system_message="你是 CBSC 量化交易專家。"
                )
            else:
                llm = None

            if llm:
                # 創建專業的量化交易聊天界面
                ai_assistant = mo.ui.chat(
                    llm,
                    prompts=[
                        "你好，我是 CBSC 量化交易 AI 助手。我可以幫您：\n\n1. 分析市場情緒數據\n2. 優化交易策略參數\n3. 評估風險指標\n4. 提供技術分析建議",
                        "基於當前的 CBSC 數據，請分析市場趨勢並提供交易建議。"
                    ],
                    placeholder="輸入您的 CBSC 交易問題...",
                    show_configuration_controls=True
                )
            else:
                ai_assistant = mo.md("⚠️ 請配置有效的 API 信息")
        else:
            ai_assistant = mo.md("⚠️ 請先配置 API Key")

    except Exception as e:
        ai_assistant = mo.md(f"❌ AI 配置錯誤: {str(e)}")

    return ai_assistant

@app.cell
def __(mo):
    """CBSC 策略參數控制"""
    rsi_period = mo.ui.slider(5, 50, value=14, label="RSI 週期")
    sentiment_threshold = mo.ui.slider(0.1, 1.0, value=0.7, step=0.05, label="情緒閾值")
    ma_short = mo.ui.slider(5, 30, value=10, label="短期均線")
    ma_long = mo.ui.slider(20, 100, value=30, label="長期均線")

    # AI 分析開關
    enable_ai_analysis = mo.ui.switch(label="啟用 AI 智能分析", value=True)

    return rsi_period, sentiment_threshold, ma_short, ma_long, enable_ai_analysis

@app.cell
def __(rsi_period, sentiment_threshold, ma_short, ma_long, enable_ai_analysis, mo):
    """CBSC 數據分析和策略計算"""
    import pandas as pd
    import numpy as np
    from pathlib import Path

    sentiment_path = "CODEX--/warrant_sentiment_daily.csv"
    data_exists = Path(sentiment_path).exists()

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

            # 生成交易信號
            conditions = [
                (df['RSI'] < 30) & (df['Sentiment_Strength'] > sentiment_threshold.value),
                (df['RSI'] > 70) & (df['Sentiment_Strength'] < -sentiment_threshold.value),
                (df['MA_Short'] > df['MA_Long']),
            ]

            signals = ['強烈買入', '強烈賣出', '買入']
            df['Strategy_Signal'] = np.select(conditions, signals, default='持有')

            # 性能計算
            df['Returns'] = df['Afternoon_Close'].pct_change()
            df['Strategy_Return'] = np.where(
                df['Strategy_Signal'].str.contains('買入'), df['Returns'] * 1.5,
                np.where(df['Strategy_Signal'].str.contains('賣出'), df['Returns'] * -1.5, 0)
            )

            cumulative_return = (1 + df['Strategy_Return'].fillna(0)).cumprod().iloc[-1] - 1
            sharpe_ratio = df['Strategy_Return'].mean() / df['Strategy_Return'].std() * np.sqrt(252) if df['Strategy_Return'].std() > 0 else 0

            signal_counts = df['Strategy_Signal'].value_counts()

            data_status = mo.md(f"""
            ✅ **CBSC 數據加載成功**

            **基本信息**:
            - 記錄數量: {len(df)} 條
            - 日期範圍: {df['Date'].min().strftime('%Y-%m-%d')} 至 {df['Date'].max().strftime('%Y-%m-%d')}
            - 平均情緒強度: {df['Sentiment_Strength'].mean():.3f}

            **當前市場狀態**:
            - 最新價格: HK${df['Afternoon_Close'].iloc[-1]:.2f}
            - 當前 RSI: {df['RSI'].iloc[-1]:.1f}
            - 情緒強度: {df['Sentiment_Strength'].iloc[-1]:.3f}
            - 當前信號: {df['Strategy_Signal'].iloc[-1]}

            **策略性能**:
            - 累計回報: {cumulative_return:.2%}
            - Sharpe 比率: {sharpe_ratio:.3f}
            - 勝率: {len(df[df['Strategy_Return'] > 0])/len(df)*100:.1f}%

            **信號分佈**:
            - 強烈買入: {signal_counts.get('強烈買入', 0)} 次
            - 買入: {signal_counts.get('買入', 0)} 次
            - 持有: {signal_counts.get('持有', 0)} 次
            - 強烈賣出: {signal_counts.get('強烈賣出', 0)} 次
            """)

        except Exception as e:
            data_status = mo.md(f"❌ 數據處理錯誤: {str(e)}")
            df = pd.DataFrame()
    else:
        data_status = mo.md("❌ CBSC 數據文件未找到")
        df = pd.DataFrame()

    return data_status, df

@app.cell
def __(df, rsi_period, sentiment_threshold, enable_ai_analysis, mo):
    """AI 智能分析和建議"""
    if df.empty:
        return mo.md("⚠️ 無數據可進行 AI 分析")

    if enable_ai_analysis.value:
        # 生成 AI 分析提示
        latest_data = df.iloc[-5:].to_dict('records')
        latest_signal = df['Strategy_Signal'].iloc[-1]
        latest_rsi = df['RSI'].iloc[-1]
        latest_sentiment = df['Sentiment_Strength'].iloc[-1]

        ai_prompt = f"""
        作為 CBSC 量化交易專家，請基於以下數據提供分析：

        **最新市場數據**:
        - RSI: {latest_rsi:.1f}
        - 情緒強度: {latest_sentiment:.3f}
        - 當前信號: {latest_signal}

        **策略參數**:
        - RSI 週期: {rsi_period.value}
        - 情緒閾值: {sentiment_threshold.value}

        **最近 5 天數據**:
        {latest_data}

        請提供：
        1. 市場趨勢分析
        2. 當前策略評估
        3. 參數優化建議
        4. 風險提示
        """

        ai_insights = mo.accordion({
            "🤖 AI 智能分析提示": f"""
            當您可以配置 AI 後，這裡將顯示基於以下數據的智能分析：

            **分析提示**: {ai_prompt}

            **使用方法**:
            1. 在上方配置 AI 提供商和 API Key
            2. 選擇合適的模型
            3. 使用聊天助手詢問具體問題
            4. 獲得專業的 CBSC 交易建議
            """
        })
    else:
        ai_insights = mo.md("AI 分析已禁用")

    return ai_insights

@app.cell
def __(mo):
    """使用說明和集成指南"""
    integration_guide = mo.accordion({
        "📖 Marimo AI 集成指南": """
        **支持的 AI 提供商**:

        1. **OpenAI**
           - 模型: gpt-4o-mini, gpt-4o, gpt-3.5-turbo
           - API Key: https://platform.openai.com/account/api-keys

        2. **Anthropic Claude**
           - 模型: claude-3-5-sonnet-20241022, claude-3-opus
           - API Key: https://console.anthropic.com/

        3. **Google AI Studio**
           - 模型: gemini-2.0-pro-exp
           - API Key: https://aistudio.google.com/app/apikey

        4. **Azure OpenAI**
           - 模型: gpt-4, gpt-35-turbo
           - 需要 Azure 資源和部署

        5. **自定義提供商**
           - 支持 OpenAI 兼容的 API
           - 配置 Base URL 和模型名稱

        **配置方法**:
        - 在界面上輸入 API Key
        - 選擇提供商和模型
        - 可選：自定義 Base URL

        **安全提示**:
        - 妥善保管 API 密鑰
        - 考虑使用環境變量存儲
        - 定期更換 API 密鑰
        """
    })

    return integration_guide

if __name__ == "__main__":
    app.run()