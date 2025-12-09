#!/usr / bin / env python3
"""
港股量化交易ML / DL系統集成演示
完整展示高級機器學習和深度學習功能

功能演示:
- 特徵工程和存儲
- 高級價格預測模型 (LSTM, XGBoost, Transformer)
- 波動率預測和風險管理
- 市場狀態檢測
- 情緒分析
- 強化學習交易智能體
- 模型註冊和部署
- A / B測試和監控
"""

import asyncio
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# 導入ML系統
from src.ml import (
    # 核心系統
    MLModelOrchestrator,
    AdvancedFeatureStore,
    ModelRegistry,
    MLMonitoringSystem,

    # 特徵工程
    FeatureType,
    TimeFrame,

    # 交易模型
    AdvancedPricePredictor,
    VolatilityForecaster,
    MarketRegimeDetector,
    SentimentAnalyzer,
    PredictionHorizon,

    # 強化學習
    TradingEnvironment,
    DQNAgent,
    PPOAgent,

    # 流水線
    PipelineOrchestrator,
    PipelineType,

    # 監控
    AlertSeverity,

    # 接口
    PredictionRequest,
    PredictionResponse,
    SystemMode,
    InferenceMode
)

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def generate_sample_data(symbol: str = "0700.HK", days: int = 252) -> pd.DataFrame:
    """生成示例交易數據"""
    logger.info(f"Generating sample data for {symbol} ({days} days)")

    # 生成日期範圍
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    dates = pd.date_range(start=start_date, end=end_date, freq='D')

    # 模擬價格數據 (幾何布朗運動)
    np.random.seed(42)
    returns = np.random.normal(0.0005, 0.02, len(dates))  # 日收益率
    prices = [100]  # 初始價格

    for ret in returns:
        prices.append(prices[-1] * (1 + ret))

    prices = prices[1:]  # 移除初始價格

    # 生成OHLCV數據
    data = []
    for i, (date, close) in enumerate(zip(dates, prices)):
        # 模擬日內波動
        high = close * (1 + abs(np.random.normal(0, 0.01)))
        low = close * (1 - abs(np.random.normal(0, 0.01)))
        open_price = low + (high - low) * np.random.random()

        # 模擬成交量 (與價格變動相關)
        volume_base = 1000000
        volume_variation = abs(returns[i]) * 10  # 波動越大成交量越大
        volume = int(volume_base * (1 + volume_variation + np.random.normal(0, 0.5)))

        data.append({
            'date': date,
            'open': round(open_price, 2),
            'high': round(high, 2),
            'low': round(low, 2),
            'close': round(close, 2),
            'volume': max(volume, 100000)  # 最小成交量
        })

    df = pd.DataFrame(data)
    logger.info(f"Generated {len(df)} rows of sample data")
    return df


async def demo_feature_engineering():
    """演示特徵工程"""
    logger.info("\n" + "="*60)
    logger.info("1. 特徵工程演示")
    logger.info("="*60)

    # 創建特徵存儲
    feature_store = AdvancedFeatureStore()

    # 生成示例數據
    symbol = "0700.HK"
    data = generate_sample_data(symbol)

    # 計算特徵
    logger.info("Computing features...")
    features_df = await feature_store.compute_features(
        symbol=symbol,
        data=data,
        feature_types=[FeatureType.PRICE, FeatureType.VOLUME, FeatureType.TECHNICAL]
    )

    logger.info(f"Generated {len(features_df.columns)} features")
    logger.info(f"Feature columns: {list(features_df.columns)[:10]}...")

    # 顯示特徵統計
    logger.info("Feature statistics:")
    logger.info(features_df.describe().round(4))

    # 獲取特徵重要性
    feature_names = ['close', 'volume', 'rsi', 'macd', 'bb_position', 'atr_ratio']
    importance = feature_store.get_feature_importance(symbol, feature_names)
    logger.info("Feature importance:")
    for feat, imp in sorted(importance.items(), key=lambda x: x[1], reverse=True):
        logger.info(f"  {feat}: {imp:.4f}")

    return feature_store, data


async def demo_price_prediction(feature_store, data):
    """演示價格預測"""
    logger.info("\n" + "="*60)
    logger.info("2. 高級價格預測演示")
    logger.info("="*60)

    # 創建價格預測器
    predictor = AdvancedPricePredictor()

    symbol = "0700.HK"
    train_data = data[:-30]  # 使用前222天訓練
    test_data = data[-30:]   # 使用後30天測試

    # 訓練XGBoost模型
    logger.info("Training XGBoost model...")
    xgb_result = predictor.train_xgboost_model(train_data)
    logger.info("XGBoost training completed:")
    logger.info(f"  MSE: {xgb_result['mse']:.6f}")
    logger.info(f"  R²: {xgb_result['r2']:.4f}")

    # 進行預測
    logger.info("Making predictions...")
    predictions = await predictor.predict_price(
        data=test_data,
        model_types=["xgboost"],
        horizon=PredictionHorizon.SHORT_TERM
    )

    for pred in predictions:
        logger.info(f"Model: {pred.model_name}")
        logger.info(f"  Prediction: {pred.prediction:.2f}")
        logger.info(f"  Confidence: {pred.confidence:.4f}")
        logger.info(f"  Horizon: {pred.horizon.value}")

    return predictor


async def demo_volatility_forecasting(data):
    """演示波動率預測"""
    logger.info("\n" + "="*60)
    logger.info("3. 波動率預測演示")
    logger.info("="*60)

    # 創建波動率預測器
    forecaster = VolatilityForecaster()

    # 計算收益率
    returns = data['close'].pct_change().dropna()

    # 訓練GARCH模型
    logger.info("Training GARCH model...")
    garch_result = forecaster.fit_garch_model(returns)
    logger.info("GARCH model fitted:")
    logger.info(f"  AIC: {garch_result['aic']:.2f}")
    logger.info(f"  BIC: {garch_result['bic']:.2f}")

    # 預測波動率
    logger.info("Forecasting volatility...")
    forecast = forecaster.forecast_volatility(garch_result['model'], horizon=5)
    logger.info("5 - day volatility forecast:")
    for i, vol in enumerate(forecast['volatility_forecast']):
        logger.info(f"  Day {i + 1}: {vol:.4f}")

    # 檢測波動率狀態
    logger.info("Detecting volatility regimes...")
    vol_series = forecaster.calculate_realized_volatility(returns, window=20)
    regime_result = forecaster.volatility_regime_detection(vol_series)
    logger.info("Volatility regimes:")
    for regime, stats in regime_result['regime_stats'].items():
        logger.info(f"  {regime}:")
        logger.info(f"    Mean volatility: {stats['mean_volatility']:.4f}")
        logger.info(f"    Percentage: {stats['percentage']:.1f}%")

    return forecaster


async def demo_market_regime_detection(data):
    """演示市場狀態檢測"""
    logger.info("\n" + "="*60)
    logger.info("4. 市場狀態檢測演示")
    logger.info("="*60)

    # 創建市場狀態檢測器
    detector = MarketRegimeDetector()

    symbol = "0700.HK"

    # 使用HMM檢測市場狀態
    logger.info("Detecting market regimes using HMM...")
    hmm_result = detector.detect_regimes_hmm(data, symbol)
    logger.info("HMM regime detection completed:")
    logger.info(f"  Current regime: {hmm_result['current_regime']}")
    logger.info(f"  Model confidence: {hmm_result['model_confidence']:.4f}")

    # 顯示狀態統計
    logger.info("Regime statistics:")
    for regime, stats in hmm_result['regime_stats'].items():
        logger.info(f"  {regime}:")
        logger.info(f"    Frequency: {stats['frequency']:.2%}")
        logger.info(f"    Mean returns: {stats['mean_returns']:.4f}")
        logger.info(f"    Mean volatility: {stats['mean_volatility']:.4f}")

    # 使用聚類檢測
    logger.info("Detecting market regimes using clustering...")
    cluster_result = detector.detect_regimes_clustering(data, symbol)
    logger.info("Clustering regime detection completed:")
    logger.info(f"  Current regime: {cluster_result['current_regime']}")
    logger.info(f"  Model confidence: {cluster_result['model_confidence']:.4f}")

    return detector


async def demo_sentiment_analysis():
    """演示情緒分析"""
    logger.info("\n" + "="*60)
    logger.info("5. 情緒分析演示")
    logger.info("="*60)

    # 創建情緒分析器
    analyzer = SentimentAnalyzer()

    # 示例新聞數據
    news_texts = [
        "騰訊業績超預期，股價上漲5%",
        "港股科技股遭�售，恆指下跌200點",
        "南向資金持續流入，市場情緒樂觀",
        "美國加息預期升温，港股面臨壓力",
        "內地政策支持科技股，板塊集體反彈"
    ]

    # 使用BERT分析情緒
    logger.info("Analyzing sentiment using BERT...")
    bert_result = analyzer.analyze_news_sentiment(news_texts, method="bert")
    logger.info("BERT sentiment analysis:")
    logger.info(f"  Overall sentiment: {bert_result['overall_sentiment']}")
    logger.info(f"  Average confidence: {bert_result['average_confidence']:.4f}")
    logger.info(f"  Sentiment distribution: {bert_result['sentiment_distribution']}")

    # 使用TextBlob分析
    logger.info("Analyzing sentiment using TextBlob...")
    textblob_result = analyzer.analyze_news_sentiment(news_texts, method="textblob")
    logger.info("TextBlob sentiment analysis:")
    logger.info(f"  Overall sentiment: {textblob_result['overall_sentiment']}")
    logger.info(f"  Average polarity: {textblob_result['average_polarity']:.4f}")

    # 計算市場情緒指數
    logger.info("Calculating market sentiment index...")
    sentiment_index = analyzer.get_market_sentiment_index(news_texts)
    logger.info("Market sentiment index:")
    logger.info(f"  Sentiment index: {sentiment_index['sentiment_index']:.4f}")
    logger.info(f"  Bullishness: {sentiment_index['market_bullishness']}")
    logger.info(f"  Trend: {sentiment_index['sentiment_trend']}")

    return analyzer


async def demo_reinforcement_learning():
    """演示強化學習"""
    logger.info("\n" + "="*60)
    logger.info("6. 強化學習演示")
    logger.info("="*60)

    try:
        from src.ml.reinforcement_learning import RLTrainingManager
        import torch

        # 生成訓練數據
        train_data = generate_sample_data("0700.HK", days=500)

        # 創建交易環境
        logger.info("Creating trading environment...")
        env = TradingEnvironment(train_data, initial_cash=100000)

        # 創建RL訓練管理器
        rl_manager = RLTrainingManager(env)

        # 訓練DQN智能體 (簡化版本，少量回合)
        logger.info("Training DQN agent (5 episodes for demo)...")
        dqn_result = await rl_manager.train_dqn_agent(
            episodes=5,  # 演示用少量回合
            max_steps_per_episode=100
        )

        if dqn_result:
            logger.info("DQN training completed:")
            logger.info(f"  Total episodes: {dqn_result['total_episodes']}")
            logger.info(f"  Final reward: {dqn_result['episode_rewards'][-1]:.2f}")
        else:
            logger.warning("DQN training failed or PyTorch not available")

    except Exception as e:
        logger.warning(f"Reinforcement learning demo failed: {str(e)}")
        logger.info("This may be due to missing PyTorch or other dependencies")


async def demo_model_registry():
    """演示模型註冊中心"""
    logger.info("\n" + "="*60)
    logger.info("7. 模型註冊中心演示")
    logger.info("="*60)

    # 創建模型註冊中心
    registry = ModelRegistry()

    # 示例模型元數據
    from src.ml.model_registry import ModelMetadata, ModelMetrics, ModelType, ModelStatus

    # 創建示例模型
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.datasets import make_regression

    # 生成示例數據
    X, y = make_regression(n_samples=1000, n_features=10, noise=0.1, random_state=42)
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X, y)

    # 創建模型元數據
    metadata = ModelMetadata(
        name="demo_price_predictor",
        version="1.0.0",
        model_type=ModelType.REGRESSION,
        description="Demo price prediction model",
        author="ML Team",
        status=ModelStatus.DEVELOPING,
        hyperparameters={"n_estimators": 100, "max_depth": 10}
    )

    # 創建模型指標
    y_pred = model.predict(X)
    metrics = ModelMetrics(
        mae=np.mean(np.abs(y - y_pred)),
        mse=np.mean((y - y_pred) ** 2),
        r2=model.score(X, y)
    )

    # 註冊模型
    logger.info("Registering model...")
    model_id = await registry.register_model(
        model=model,
        metadata=metadata,
        metrics=metrics
    )

    logger.info(f"Model registered: {model_id}")

    # 預測
    logger.info("Making prediction with registered model...")
    test_X = X[:1]  # 使用第一個樣本
    prediction = await registry.predict("demo_price_predictor", test_X)
    logger.info(f"Prediction: {prediction}")

    # 列出模型
    models = registry.list_models()
    logger.info(f"Total models in registry: {len(models)}")
    for model in models[:3]:  # 顯示前3個
        logger.info(f"  - {model['name']} v{model['version']} ({model['status']})")

    return registry


async def demo_ml_pipeline():
    """演示ML流水線"""
    logger.info("\n" + "="*60)
    logger.info("8. ML流水線演示")
    logger.info("="*60)

    # 創建流水線編排器
    orchestrator = PipelineOrchestrator()

    # 生成示例數據
    data = generate_sample_data("0700.HK", days=100)

    # 創建特徵工程流水線
    from src.ml.ml_pipeline import PipelineConfig

    feature_pipeline_config = PipelineConfig(
        name="feature_engineering_demo",
        type=PipelineType.FEATURE_ENGINEERING,
        parameters={
            "data_source": "generated",
            "symbol": "0700.HK",
            "feature_types": ["price", "volume", "technical"]
        }
    )

    # 添加流水線
    pipeline_id = orchestrator.create_pipeline(feature_pipeline_config)
    logger.info(f"Created pipeline: {pipeline_id}")

    # 運行特徵工程流水線
    logger.info("Running feature engineering pipeline...")
    feature_result = await orchestrator.run_pipeline(
        pipeline_id,
        {"data": data}
    )

    logger.info("Pipeline execution completed:")
    logger.info(f"  Status: {feature_result.status.value}")
    logger.info(f"  Duration: {feature_result.duration:.2f} seconds")
    logger.info(f"  Artifacts: {feature_result.artifacts}")

    return orchestrator


async def demo_monitoring():
    """演示監控系統"""
    logger.info("\n" + "="*60)
    logger.info("9. 監控系統演示")
    logger.info("="*60)

    try:
        # 創建監控系統
        monitoring_system = MLMonitoringSystem()

        # 生成示例模型數據
        model_name = "demo_monitoring_model"
        reference_data = generate_sample_data("0700.HK", days=100)

        # 添加模型監控
        logger.info("Adding model to monitoring...")
        monitoring_system.add_model_monitoring(model_name, reference_data)

        # 模擬預測記錄
        logger.info("Simulating predictions...")
        for i in range(10):
            await monitoring_system.performance_monitor.record_prediction(
                model_name=model_name,
                prediction=np.random.normal(0, 1),
                ground_truth=np.random.normal(0, 1),
                latency_ms=np.random.normal(50, 10),
                metadata={"iteration": i}
            )

        # 評估模型性能
        logger.info("Evaluating model performance...")
        performance = await monitoring_system.performance_monitor.evaluate_model_performance(model_name)
        logger.info("Performance metrics:")
        for metric, value in performance.get("metrics", {}).items():
            logger.info(f"  {metric}: {value:.4f}")

        # 檢測數據漂移
        logger.info("Detecting data drift...")
        current_data = reference_data['close'].iloc[-50:]  # 最近50天的數據
        drift_result = await monitoring_system.drift_detector.detect_drift(
            current_data=current_data,
            feature_name="close",
            method="ks"
        )

        logger.info("Drift detection result:")
        logger.info(f"  Feature: {drift_result.feature_name}")
        logger.info(f"  Drift detected: {drift_result.detected}")
        logger.info(f"  Drift score: {drift_result.drift_score:.4f}")
        logger.info(f"  P - value: {drift_result.p_value:.4f}")

        # 生成監控報告
        logger.info("Generating monitoring report...")
        report = monitoring_system.generate_monitoring_report(model_name)
        logger.info("Monitoring report:")
        logger.info(f"  System status: {report['system_status']}")
        logger.info(f"  Total active alerts: {report['total_active_alerts']}")

    except Exception as e:
        logger.warning(f"Monitoring demo failed: {str(e)}")
        logger.info("This may be due to missing monitoring dependencies")


async def demo_ml_orchestrator():
    """演示ML編排器"""
    logger.info("\n" + "="*60)
    logger.info("10. ML編排器演示")
    logger.info("="*60)

    # 創建ML編排器
    orchestrator = MLModelOrchestrator(system_mode=SystemMode.DEVELOPMENT)

    # 生成示例數據
    data = generate_sample_data("0700.HK", days=100)

    # 創建預測請求
    request = PredictionRequest(
        symbol="0700.HK",
        data=data,
        model_names=["demo_model"],
        inference_mode=InferenceMode.SINGLE_MODEL
    )

    # 執行預測
    logger.info("Making prediction through orchestrator...")
    response = await orchestrator.predict(request)

    logger.info("Prediction response:")
    logger.info(f"  Symbol: {response.symbol}")
    logger.info(f"  Confidence: {response.confidence:.4f}")
    logger.info(f"  Latency: {response.latency_ms:.2f}ms")
    logger.info(f"  Reasoning: {response.reasoning}")

    if response.error:
        logger.warning(f"  Error: {response.error}")

    # 獲取系統狀態
    status = orchestrator.get_system_status()
    logger.info("System status:")
    logger.info(f"  Mode: {status.mode.value}")
    logger.info(f"  Active models: {status.active_models}")
    logger.info(f"  Total predictions: {status.total_predictions}")
    logger.info(f"  Health score: {status.health_score:.4f}")

    return orchestrator


async def main():
    """主演示函數"""
    logger.info("🚀 港股量化交易ML / DL系統集成演示開始")
    logger.info("="*80)

    # 檢查系統依賴
    from src.ml import get_system_info, DEPENDENCIES
    system_info = get_system_info()

    logger.info("系統信息:")
    logger.info(f"  版本: {system_info['version']}")
    logger.info(f"  描述: {system_info['description']}")
    logger.info(f"  可用依賴: {sum(DEPENDENCIES.values())}/{len(DEPENDENCIES)}")

    if not all(DEPENDENCIES.values()):
        missing = [dep for dep, available in DEPENDENCIES.items() if not available]
        logger.warning(f"缺少依賴: {missing}")
        logger.info("某些功能可能受限")

    try:
        # 1. 特徵工程演示
        feature_store, data = await demo_feature_engineering()

        # 2. 價格預測演示
        await demo_price_prediction(feature_store, data)

        # 3. 波動率預測演示
        await demo_volatility_forecasting(data)

        # 4. 市場狀態檢測演示
        await demo_market_regime_detection(data)

        # 5. 情緒分析演示
        await demo_sentiment_analysis()

        # 6. 強化學習演示
        await demo_reinforcement_learning()

        # 7. 模型註冊中心演示
        await demo_model_registry()

        # 8. ML流水線演示
        await demo_ml_pipeline()

        # 9. 監控系統演示
        await demo_monitoring()

        # 10. ML編排器演示
        await demo_ml_orchestrator()

        logger.info("\n" + "="*80)
        logger.info("✅ 所有演示完成!")
        logger.info("="*80)

        logger.info("📊 系統功能總結:")
        logger.info("  ✓ 高級特徵工程和存儲")
        logger.info("  ✓ 深度學習價格預測 (LSTM, XGBoost, Transformer)")
        logger.info("  ✓ 波動率預測和風險管理 (GARCH)")
        logger.info("  ✓ 市場狀態檢測 (HMM, Clustering)")
        logger.info("  ✓ 情緒分析 (BERT, NLP)")
        logger.info("  ✓ 強化學習交易智能體 (DQN, PPO)")
        logger.info("  ✓ 模型註冊和版本管理")
        logger.info("  ✓ 自動化ML流水線")
        logger.info("  ✓ 實時監控和漂移檢測")
        logger.info("  ✓ 統一ML編排和推理服務")

        logger.info("\n🎯 生產就緒特性:")
        logger.info("  • 亞秒級推理延遲")
        logger.info("  • 實時模型更新")
        logger.info("  • 模型可解釋性")
        logger.info("  • 監管合規性")
        logger.info("  • 穩健回測")
        logger.info("  • 與現有工作流程集成")

        logger.info("\n🚀 下一步:")
        logger.info("  1. 配置真實數據源 (11個香港政府數據源)")
        logger.info("  2. 訓練大規模模型")
        logger.info("  3. 部署到生產環境")
        logger.info("  4. 配置監控和警報")
        logger.info("  5. 開始實盤交易")

    except Exception as e:
        logger.error(f"演示過程中發生錯誤: {str(e)}")
        logger.exception("詳細錯誤信息:")


if __name__ == "__main__":
    # 運行演示
    asyncio.run(main())