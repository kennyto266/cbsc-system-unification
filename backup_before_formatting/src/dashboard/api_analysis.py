# -*- coding: utf-8 -*-
"""
分析服務API
提供技術分析、基本面分析、機器學習預測等8個端點
"""

import asyncio
import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from ..data_adapters.base_adapter import BaseAdapter
from ..ml.prediction_engine import MLPredictionEngine, ModelType, PredictionHorizon
from ..signals.intelligent_signals import IntelligentSignalGenerator
from .models.api_response import APIResponse

# ========== Pydantic 模型 ==========


class AnalysisType(str, Enum):
    """分析類型"""

    TECHNICAL = "technical"
    FUNDAMENTAL = "fundamental"
    QUANTITATIVE = "quantitative"
    SENTIMENT = "sentiment"


class ForecastRequest(BaseModel):
    """預測請求"""

    symbol: str = Field(..., description="股票代碼")
    model_type: str = Field(default="hybrid", description="模型類型")
    horizon_days: int = Field(default=5, ge=1, le=60, description="預測天數")
    confidence_threshold: float = Field(
        default=0.6, ge=0.5, le=0.95, description="信心閾值"
    )


class CorrelationRequest(BaseModel):
    """相關性分析請求"""

    symbols: List[str] = Field(..., min_items=2, max_items=50, description="股票列表")
    period: int = Field(default=252, ge=30, le=2520, description="分析期間 (天)")
    method: str = Field(default="pearson", description="相關性方法")


class StressTestRequest(BaseModel):
    """壓力測試請求"""

    symbols: List[str] = Field(..., description="股票列表")
    scenarios: List[Dict[str, Any]] = Field(..., description="壓力場景")
    confidence_level: float = Field(default=0.95, description="置信水平")


class PriceAnalysisResponse(BaseModel):
    """價格分析響應"""

    symbol: str
    current_price: float
    price_change: float
    price_change_pct: float
    volume: float
    volatility: float
    support_level: float
    resistance_level: float
    trend_direction: str
    analysis_date: datetime


class ForecastResponse(BaseModel):
    """預測響應"""

    symbol: str
    model_type: str
    horizon_days: int
    predicted_price: float
    confidence: float
    upper_bound: float
    lower_bound: float
    trend: str
    risk_level: str
    forecast_date: datetime


class TechnicalIndicatorsResponse(BaseModel):
    """技術指標響應"""

    symbol: str
    rsi: Optional[float] = None
    macd: Optional[float] = None
    macd_signal: Optional[float] = None
    bb_upper: Optional[float] = None
    bb_middle: Optional[float] = None
    bb_lower: Optional[float] = None
    sma_5: Optional[float] = None
    sma_20: Optional[float] = None
    sma_60: Optional[float] = None
    atr: Optional[float] = None
    stochastic_k: Optional[float] = None
    stochastic_d: Optional[float] = None
    adx: Optional[float] = None
    obv: Optional[float] = None
    analysis_date: datetime


class CorrelationMatrixResponse(BaseModel):
    """相關性矩陣響應"""

    symbols: List[str]
    matrix: List[List[float]]
    strongest_correlation: Dict[str, Any]
    average_correlation: float
    period_days: int
    analysis_date: datetime


class VolatilityAnalysisResponse(BaseModel):
    """波動率分析響應"""

    symbol: str
    current_volatility: float
    historical_volatility: Dict[str, float]  # 1M, 3M, 6M, 1Y
    implied_volatility: Optional[float]
    volatility_percentile: float
    garch_forecast: Optional[Dict[str, float]]
    var_95: Optional[float]  # 95% VaR
    analysis_date: datetime


class BacktestRequest(BaseModel):
    """回測請求"""

    symbol: str = Field(..., description="股票代碼")
    strategy: str = Field(..., description="策略名稱")
    start_date: str = Field(..., description="開始日期")
    end_date: str = Field(..., description="結束日期")
    initial_capital: float = Field(default=1000000, description="初始資金")
    parameters: Optional[Dict[str, Any]] = Field(None, description="策略參數")


class BacktestResponse(BaseModel):
    """回測響應"""

    strategy: str
    symbol: str
    period: str
    total_return: float
    annualized_return: float
    volatility: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    total_trades: int
    profit_factor: float
    calmar_ratio: float
    analysis_date: datetime


class PerformanceAttributionResponse(BaseModel):
    """績效歸因響應"""

    symbol: str
    total_return: float
    attribution: Dict[str, float]  # 各因子貢獻
    allocation_effect: float
    selection_effect: float
    interaction_effect: float
    benchmark_return: float
    excess_return: float
    analysis_date: datetime


class StressTestResponse(BaseModel):
    """壓力測試響應"""

    scenarios: List[Dict[str, Any]]
    portfolio_value: float
    scenario_results: List[Dict[str, Any]]
    worst_case_loss: float
    var_95: float
    var_99: float
    expected_shortfall: float
    analysis_date: datetime


# ========== 技術分析工具 ==========


class TechnicalAnalysisEngine:
    """技術分析引擎"""

    @staticmethod
    def calculate_rsi(prices: pd.Series, period: int = 14) -> float:
        """計算RSI"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi.iloc[-1] if not pd.isna(rsi.iloc[-1]) else 50.0

    @staticmethod
    def calculate_macd(prices: pd.Series) -> Tuple[float, float, float]:
        """計算MACD"""
        ema_12 = prices.ewm(span=12).mean()
        ema_26 = prices.ewm(span=26).mean()
        macd = ema_12 - ema_26
        signal = macd.ewm(span=9).mean()
        histogram = macd - signal
        return macd.iloc[-1], signal.iloc[-1], histogram.iloc[-1]

    @staticmethod
    def calculate_bollinger_bands(
        prices: pd.Series, period: int = 20, std_dev: int = 2
    ) -> Tuple[float, float, float, float]:
        """計算布林帶"""
        sma = prices.rolling(period).mean()
        std = prices.rolling(period).std()
        upper = sma + (std * std_dev)
        lower = sma - (std * std_dev)
        position = (prices.iloc[-1] - lower.iloc[-1]) / (
            upper.iloc[-1] - lower.iloc[-1]
        )
        return upper.iloc[-1], sma.iloc[-1], lower.iloc[-1], position

    @staticmethod
    def calculate_moving_averages(prices: pd.Series) -> Dict[str, float]:
        """計算移動平均線"""
        return {
            "sma_5": prices.rolling(5).mean().iloc[-1],
            "sma_20": prices.rolling(20).mean().iloc[-1],
            "sma_60": prices.rolling(60).mean().iloc[-1],
        }

    @staticmethod
    def calculate_atr(
        high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14
    ) -> float:
        """計算ATR"""
        high_low = high - low
        high_close = np.abs(high - close.shift())
        low_close = np.abs(low - close.shift())
        ranges = np.maximum(high_low, np.maximum(high_close, low_close))
        atr = ranges.rolling(period).mean()
        return atr.iloc[-1]


# ========== FastAPI 路由 ==========


def create_analysis_router(
    data_adapter: BaseAdapter,
    ml_engine: Optional[MLPredictionEngine] = None,
    signal_generator: Optional[IntelligentSignalGenerator] = None,
) -> APIRouter:
    """創建分析服務路由"""
    router = APIRouter(prefix="/api / v2 / analysis", tags=["analysis"])
    logger = logging.getLogger("hk_quant_system.analysis_api")

    @router.get("/price/{symbol}", response_model=APIResponse)
    async def analyze_price(
        symbol: str, period: int = Query(default=30, description="分析期間 (天)")
    ):
        """價格分析"""
        try:
            # 獲取歷史數據
            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now() - timedelta(days=period + 30)).strftime(
                "%Y-%m-%d"
            )

            data = await data_adapter.fetch_data(symbol, start_date, end_date)
            df = pd.DataFrame(data)
            df["date"] = pd.to_datetime(df["date"])
            df = df.sort_values("date").tail(period)

            if len(df) == 0:
                raise HTTPException(status_code=404, detail=f"沒有找到 {symbol} 的數據")

            current_price = float(df["close"].iloc[-1])
            previous_price = float(df["close"].iloc[0])
            price_change = current_price - previous_price
            price_change_pct = (price_change / previous_price) * 100

            # 計算波動率
            returns = df["close"].pct_change().dropna()
            volatility = returns.std() * np.sqrt(252)

            # 計算支撐和阻力
            support_level = df["low"].rolling(20).min().iloc[-1]
            resistance_level = df["high"].rolling(20).max().iloc[-1]

            # 判斷趨勢
            sma_20 = df["close"].rolling(20).mean().iloc[-1]
            if current_price > sma_20:
                trend = "up"
            elif current_price < sma_20:
                trend = "down"
            else:
                trend = "sideways"

            analysis = PriceAnalysisResponse(
                symbol=symbol,
                current_price=current_price,
                price_change=price_change,
                price_change_pct=price_change_pct,
                volume=float(df["volume"].iloc[-1]),
                volatility=volatility,
                support_level=support_level,
                resistance_level=resistance_level,
                trend_direction=trend,
                analysis_date=datetime.now(),
            )

            return APIResponse(
                success=True, data=analysis.dict(), message=f"{symbol} 價格分析完成"
            )

        except Exception as e:
            logger.error(f"價格分析失敗: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.post("/forecast", response_model=APIResponse)
    async def forecast_prices(request: ForecastRequest):
        """價格預測"""
        try:
            if not ml_engine:
                raise HTTPException(status_code=503, detail="機器學習引擎未初始化")

            # 使用ML引擎預測
            horizon_map = {
                1: PredictionHorizon.SHORT_TERM,
                5: PredictionHorizon.SHORT_TERM,
                20: PredictionHorizon.MEDIUM_TERM,
                60: PredictionHorizon.LONG_TERM,
            }

            prediction = await ml_engine.predict_price(
                symbol=request.symbol,
                model_type=ModelType.HYBRID,
                horizon=horizon_map.get(
                    request.horizon_days, PredictionHorizon.SHORT_TERM
                ),
                days_ahead=request.horizon_days,
            )

            if not prediction:
                raise HTTPException(status_code=500, detail="預測失敗")

            # 獲取當前價格
            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
            data = await data_adapter.fetch_data(request.symbol, start_date, end_date)
            current_price = float(data[-1]["close"]) if data else 100.0

            # 計算上下界
            confidence_interval = (
                1.96 * prediction.volatility * current_price
            )  # 95 % 置信區間
            upper_bound = prediction.predicted_price + confidence_interval
            lower_bound = prediction.predicted_price - confidence_interval

            forecast = ForecastResponse(
                symbol=request.symbol,
                model_type=request.model_type,
                horizon_days=request.horizon_days,
                predicted_price=prediction.predicted_price,
                confidence=prediction.confidence,
                upper_bound=upper_bound,
                lower_bound=lower_bound,
                trend=prediction.trend_direction,
                risk_level=prediction.risk_level,
                forecast_date=datetime.now(),
            )

            return APIResponse(
                success=True,
                data=forecast.dict(),
                message=f"{request.symbol} 價格預測完成",
            )

        except Exception as e:
            logger.error(f"價格預測失敗: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/indicators", response_model=APIResponse)
    async def get_technical_indicators(
        symbol: str, period: int = Query(default=60, description="計算期間")
    ):
        """技術指標"""
        try:
            # 獲取歷史數據
            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now() - timedelta(days=period + 30)).strftime(
                "%Y-%m-%d"
            )

            data = await data_adapter.fetch_data(symbol, start_date, end_date)
            df = pd.DataFrame(data)
            df["date"] = pd.to_datetime(df["date"])
            df = df.sort_values("date").tail(period)

            if len(df) < 20:
                raise HTTPException(status_code=400, detail="數據不足")

            # 計算技術指標
            engine = TechnicalAnalysisEngine()

            rsi = engine.calculate_rsi(df["close"])
            macd, macd_signal, macd_histogram = engine.calculate_macd(df["close"])
            bb_upper, bb_middle, bb_lower, bb_position = (
                engine.calculate_bollinger_bands(df["close"])
            )
            ma_dict = engine.calculate_moving_averages(df["close"])
            atr = engine.calculate_atr(df["high"], df["low"], df["close"])

            # 計算隨機指標
            low_14 = df["low"].rolling(14).min()
            high_14 = df["high"].rolling(14).max()
            k_percent = 100 * ((df["close"] - low_14) / (high_14 - low_14))
            d_percent = k_percent.rolling(3).mean()

            indicators = TechnicalIndicatorsResponse(
                symbol=symbol,
                rsi=rsi,
                macd=macd,
                macd_signal=macd_signal,
                bb_upper=bb_upper,
                bb_middle=bb_middle,
                bb_lower=bb_lower,
                sma_5=ma_dict["sma_5"],
                sma_20=ma_dict["sma_20"],
                sma_60=ma_dict["sma_60"],
                atr=atr,
                stochastic_k=k_percent.iloc[-1],
                stochastic_d=d_percent.iloc[-1],
                adx=25.0,  # 簡化
                obv=0.0,  # 簡化
                analysis_date=datetime.now(),
            )

            return APIResponse(
                success=True,
                data=indicators.dict(),
                message=f"{symbol} 技術指標計算完成",
            )

        except Exception as e:
            logger.error(f"技術指標計算失敗: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.post("/correlation", response_model=APIResponse)
    async def analyze_correlation(request: CorrelationRequest):
        """相關性分析"""
        try:
            # 獲取各股票數據
            all_data = {}
            for symbol in request.symbols:
                end_date = datetime.now().strftime("%Y-%m-%d")
                start_date = (
                    datetime.now() - timedelta(days=request.period + 30)
                ).strftime("%Y-%m-%d")

                data = await data_adapter.fetch_data(symbol, start_date, end_date)
                df = pd.DataFrame(data)
                df["date"] = pd.to_datetime(df["date"])
                df = df.sort_values("date").tail(request.period)
                all_data[symbol] = df["close"]

            # 計算收益率
            returns_df = pd.DataFrame(all_data).pct_change().dropna()

            # 計算相關性矩陣
            correlation_matrix = returns_df.corr(method=request.method)

            # 找出最強相關性
            mask = np.triu(np.ones_like(correlation_matrix, dtype=bool))
            correlation_matrix_masked = correlation_matrix.mask(mask)
            correlation_values = correlation_matrix_masked.unstack().dropna()

            if not correlation_values.empty:
                strongest = correlation_values.abs().idxmax()
                strongest_value = correlation_values[strongest]
            else:
                strongest = (request.symbols[0], request.symbols[1])
                strongest_value = 0.0

            # 計算平均相關性
            avg_correlation = correlation_matrix.values[
                np.triu_indices_from(correlation_matrix.values, k=1)
            ].mean()

            response = CorrelationMatrixResponse(
                symbols=request.symbols,
                matrix=correlation_matrix.values.tolist(),
                strongest_correlation={
                    "pair": strongest,
                    "correlation": float(strongest_value),
                },
                average_correlation=float(avg_correlation),
                period_days=request.period,
                analysis_date=datetime.now(),
            )

            return APIResponse(
                success=True, data=response.dict(), message="相關性分析完成"
            )

        except Exception as e:
            logger.error(f"相關性分析失敗: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/volatility/{symbol}", response_model=APIResponse)
    async def analyze_volatility(
        symbol: str, period: int = Query(default=252, description="分析期間")
    ):
        """波動率分析"""
        try:
            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now() - timedelta(days=period + 60)).strftime(
                "%Y-%m-%d"
            )

            data = await data_adapter.fetch_data(symbol, start_date, end_date)
            df = pd.DataFrame(data)
            df["date"] = pd.to_datetime(df["date"])
            df = df.sort_values("date")

            # 計算收益率
            returns = df["close"].pct_change().dropna()

            # 當前波動率
            current_vol = returns.tail(30).std() * np.sqrt(252)

            # 歷史波動率
            historical_vol = {
                "1M": returns.tail(30).std() * np.sqrt(252),
                "3M": returns.tail(90).std() * np.sqrt(252),
                "6M": returns.tail(180).std() * np.sqrt(252),
                "1Y": returns.tail(252).std() * np.sqrt(252),
            }

            # 波動率分位數
            vol_percentile = (
                returns.tail(252).std() * np.sqrt(252) < current_vol
            ) * 100

            # VaR計算
            var_95 = np.percentile(returns.tail(252), 5) * df["close"].iloc[-1]

            response = VolatilityAnalysisResponse(
                symbol=symbol,
                current_volatility=float(current_vol),
                historical_volatility={k: float(v) for k, v in historical_vol.items()},
                implied_volatility=None,  # 簡化
                volatility_percentile=float(vol_percentile),
                garch_forecast=None,  # 簡化
                var_95=float(var_95),
                analysis_date=datetime.now(),
            )

            return APIResponse(
                success=True, data=response.dict(), message=f"{symbol} 波動率分析完成"
            )

        except Exception as e:
            logger.error(f"波動率分析失敗: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.post("/backtest", response_model=APIResponse)
    async def run_backtest(request: BacktestRequest):
        """回測分析"""
        try:
            # 獲取歷史數據
            data = await data_adapter.fetch_data(
                request.symbol, request.start_date, request.end_date
            )
            df = pd.DataFrame(data)
            df["date"] = pd.to_datetime(df["date"])
            df = df.sort_values("date")

            if len(df) < 30:
                raise HTTPException(status_code=400, detail="回測數據不足")

            # 簡化回測 (實際中會使用真實的策略)
            initial_capital = request.initial_capital
            capital = initial_capital
            position = 0
            trades = []
            equity_curve = [initial_capital]

            for i in range(1, len(df)):
                current_price = df["close"].iloc[i]
                prev_price = df["close"].iloc[i - 1]

                # 簡單策略：價格上漲買入，下跌賣出
                if prev_price < current_price and position == 0:
                    # 買入
                    shares = capital // current_price
                    position = shares
                    cost = shares * current_price
                    capital -= cost
                    trades.append(
                        {
                            "date": df["date"].iloc[i],
                            "action": "buy",
                            "price": current_price,
                            "shares": shares,
                            "cost": cost,
                        }
                    )
                elif prev_price > current_price and position > 0:
                    # 賣出
                    revenue = position * current_price
                    capital += revenue
                    trades.append(
                        {
                            "date": df["date"].iloc[i],
                            "action": "sell",
                            "price": current_price,
                            "shares": position,
                            "revenue": revenue,
                        }
                    )
                    position = 0

                # 計算當前權益
                current_equity = capital + (position * current_price)
                equity_curve.append(current_equity)

            # 計算績效指標
            total_return = (equity_curve[-1] / initial_capital - 1) * 100
            annualized_return = (equity_curve[-1] / initial_capital) ** (
                365 / len(df)
            ) - 1
            volatility = np.std(
                [
                    equity_curve[i] / equity_curve[i - 1] - 1
                    for i in range(1, len(equity_curve))
                ]
            ) * np.sqrt(252)
            sharpe_ratio = annualized_return / volatility if volatility > 0 else 0

            # 最大回撤
            peak = np.maximum.accumulate(equity_curve)
            drawdown = (equity_curve - peak) / peak
            max_drawdown = abs(min(drawdown)) * 100

            # 勝率 (簡化)
            win_rate = 60.0  # 簡化

            response = BacktestResponse(
                strategy=request.strategy,
                symbol=request.symbol,
                period=f"{request.start_date} 至 {request.end_date}",
                total_return=total_return,
                annualized_return=annualized_return * 100,
                volatility=volatility * 100,
                sharpe_ratio=sharpe_ratio,
                max_drawdown=max_drawdown,
                win_rate=win_rate,
                total_trades=len(trades),
                profit_factor=1.5,  # 簡化
                calmar_ratio=(
                    annualized_return / max_drawdown if max_drawdown > 0 else 0
                ),
                analysis_date=datetime.now(),
            )

            return APIResponse(
                success=True, data=response.dict(), message=f"{request.symbol} 回測完成"
            )

        except Exception as e:
            logger.error(f"回測分析失敗: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/performance/{symbol}", response_model=APIResponse)
    async def analyze_performance_attribution(
        symbol: str, benchmark: str = Query(default="0700.hk", description="基準股票")
    ):
        """績效歸因"""
        try:
            # 獲取股票和基準數據
            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now() - timedelta(days=252)).strftime("%Y-%m-%d")

            stock_data = await data_adapter.fetch_data(symbol, start_date, end_date)
            benchmark_data = await data_adapter.fetch_data(
                benchmark, start_date, end_date
            )

            stock_df = pd.DataFrame(stock_data).sort_values("date")
            benchmark_df = pd.DataFrame(benchmark_data).sort_values("date")

            # 計算收益率
            stock_returns = stock_df["close"].pct_change().dropna()
            benchmark_returns = benchmark_df["close"].pct_change().dropna()

            total_return = (
                stock_df["close"].iloc[-1] / stock_df["close"].iloc[0] - 1
            ) * 100
            benchmark_return = (
                benchmark_df["close"].iloc[-1] / benchmark_df["close"].iloc[0] - 1
            ) * 100
            excess_return = total_return - benchmark_return

            # 簡化歸因分析
            attribution = {
                "market_effect": benchmark_return,
                "selection_effect": excess_return * 0.6,
                "timing_effect": excess_return * 0.4,
            }

            response = PerformanceAttributionResponse(
                symbol=symbol,
                total_return=total_return,
                attribution=attribution,
                allocation_effect=0.0,  # 簡化
                selection_effect=attribution["selection_effect"],
                interaction_effect=0.0,  # 簡化
                benchmark_return=benchmark_return,
                excess_return=excess_return,
                analysis_date=datetime.now(),
            )

            return APIResponse(
                success=True, data=response.dict(), message=f"{symbol} 績效歸因分析完成"
            )

        except Exception as e:
            logger.error(f"績效歸因分析失敗: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.post("/stress - test", response_model=APIResponse)
    async def run_stress_test(request: StressTestRequest):
        """壓力測試"""
        try:
            # 獲取當前組合價值 (簡化)
            portfolio_value = 1000000.0

            # 執行壓力場景
            scenario_results = []
            for scenario in request.scenarios:
                scenario_name = scenario.get("name", "Unknown")
                market_shock = scenario.get("market_shock", 0)  # 市場衝擊百分比
                volatility_change = scenario.get("volatility_change", 0)  # 波動率變化

                # 計算影響
                scenario_value = portfolio_value * (1 + market_shock / 100)
                scenario_pnl = scenario_value - portfolio_value

                scenario_results.append(
                    {
                        "scenario": scenario_name,
                        "market_shock": market_shock,
                        "new_value": scenario_value,
                        "pnl": scenario_pnl,
                        "pnl_pct": (scenario_pnl / portfolio_value) * 100,
                    }
                )

            # 找出最壞情況
            worst_case = min(scenario_results, key=lambda x: x["pnl"])
            worst_case_loss = abs(worst_case["pnl"])

            # 計算VaR (簡化)
            var_95 = portfolio_value * 0.05  # 5% VaR
            var_99 = portfolio_value * 0.08  # 8% VaR
            expected_shortfall = portfolio_value * 0.06  # 期望短缺

            response = StressTestResponse(
                scenarios=request.scenarios,
                portfolio_value=portfolio_value,
                scenario_results=scenario_results,
                worst_case_loss=worst_case_loss,
                var_95=var_95,
                var_99=var_99,
                expected_shortfall=expected_shortfall,
                analysis_date=datetime.now(),
            )

            return APIResponse(
                success=True, data=response.dict(), message="壓力測試完成"
            )

        except Exception as e:
            logger.error(f"壓力測試失敗: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    return router
