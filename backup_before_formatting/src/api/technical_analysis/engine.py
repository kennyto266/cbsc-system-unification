"""
技術分析指標計算引擎
Technical Analysis Indicator Calculation Engine
"""

import asyncio
import json
import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiofiles
import numpy as np
import pandas as pd
import requests

from .models import (
    BatchRequest,
    BollingerBandsAnalysis,
    BollingerBandsRequest,
    BollingerBandsResponse,
    BollingerBandsValue,
    DataConverter,
    DataSourceType,
    DateRange,
    IndicatorType,
    MACDRequest,
    MACDResponse,
    MACDSignals,
    MACDValue,
    QualityMetrics,
    RSIRequest,
    RSIResponse,
    RSIStatistics,
    RSIValue,
    SignalType,
)

logger = logging.getLogger(__name__)


class TechnicalIndicatorEngine:
    """技術指標計算引擎"""

    def __init__(self, cache_ttl_seconds: int = 1800):
        """初始化計算引擎"""
        self.cache = {}
        self.cache_ttl = cache_ttl_seconds
        self.data_cache = {}

        # 數據源配置
        self.data_sources = {
            DataSourceType.HIBOR_OVERNIGHT: {
                "api_endpoint": "http://localhost:8002/data/hibor_overnight/latest",
                "data_file": "data/daily_real_data/hibor_overnight_20251122.json",
                "field": "rate"
            },
            DataSourceType.MONETARY_BASE: {
                "api_endpoint": "http://localhost:8002/data/monetary_base/latest",
                "data_file": "data/daily_real_data/monetary_base_20251122.json",
                "field": "amount"
            },
            DataSourceType.GDP_GROWTH: {
                "api_endpoint": "http://localhost:8002/data/gdp_growth/latest",
                "data_file": "data/daily_real_data/gdp_growth_20251122.json",
                "field": "growth_rate"
            },
            DataSourceType.UNEMPLOYMENT_RATE: {
                "api_endpoint": "http://localhost:8002/data/unemployment_rate/latest",
                "data_file": "data/daily_real_data/unemployment_rate_20251122.json",
                "field": "rate"
            }
        }

    async def fetch_data(self, source: DataSourceType, date_range: DateRange) -> pd.Series:
        """獲取指定數據源的數據"""
        try:
            # 首先嘗試從API獲取
            if source in self.data_sources:
                endpoint = self.data_sources[source]["api_endpoint"]
                data = await self._fetch_from_api(endpoint, date_range)
                if data is not None and not data.empty:
                    return data

            # 如果API失敗，從本地文件獲取
            if source in self.data_sources:
                data_file = self.data_sources[source]["data_file"]
                field = self.data_sources[source]["field"]
                data = await self._load_from_file(data_file, field, date_range)
                if data is not None and not data.empty:
                    return data

            # 生成模擬數據作為最後手段
            logger.warning(f"Using simulated data for {source}")
            return self._generate_simulated_data(source, date_range)

        except Exception as e:
            logger.error(f"Error fetching data for {source}: {e}")
            return self._generate_simulated_data(source, date_range)

    async def _fetch_from_api(self, endpoint: str, date_range: DateRange) -> Optional[pd.Series]:
        """從API獲取數據"""
        try:
            response = requests.get(endpoint, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if "records" in data and data["records"]:
                    # 將記錄轉換為DataFrame
                    df = pd.DataFrame(data["records"])
                    df['date'] = pd.to_datetime(df['date'])

                    # 過濾日期範圍
                    start_date = pd.to_datetime(date_range.start_date)
                    end_date = pd.to_datetime(date_range.end_date)
                    mask = (df['date'] >= start_date) & (df['date'] <= end_date)
                    df = df[mask]

                    if not df.empty and 'value' in df.columns:
                        df.set_index('date', inplace=True)
                        return pd.to_numeric(df['value'], errors='coerce').dropna()

        except Exception as e:
            logger.error(f"API fetch failed: {e}")

        return None

    async def _load_from_file(self, file_path: str, field: str, date_range: DateRange) -> Optional[pd.Series]:
        """從本地文件加載數據"""
        try:
            path = Path(file_path)
            if path.exists():
                async with aiofiles.open(path, encoding='utf-8') as f:
                    content = await f.read()
                    data = json.loads(content)

                if "records" in data and data["records"]:
                    df = pd.DataFrame(data["records"])
                    df['date'] = pd.to_datetime(df['date'])

                    # 過濾日期範圍
                    start_date = pd.to_datetime(date_range.start_date)
                    end_date = pd.to_datetime(date_range.end_date)
                    mask = (df['date'] >= start_date) & (df['date'] <= end_date)
                    df = df[mask]

                    if not df.empty and field in df.columns:
                        df.set_index('date', inplace=True)
                        return pd.to_numeric(df[field], errors='coerce').dropna()

        except Exception as e:
            logger.error(f"File load failed: {e}")

        return None

    def _generate_simulated_data(self, source: DataSourceType, date_range: DateRange) -> pd.Series:
        """生成模擬數據"""
        start_date = pd.to_datetime(date_range.start_date)
        end_date = pd.to_datetime(date_range.end_date)
        dates = pd.date_range(start_date, end_date, freq='D')

        # 根據數據源類型生成不同特徵的模擬數據
        np.random.seed(42)  # 確保可重複性

        if source == DataSourceType.HIBOR_OVERNIGHT:
            # HIBOR: 圍繞3.5%波動
            base_value = 3.5
            volatility = 0.5
            trend = np.linspace(0, 0.2, len(dates))
        elif source == DataSourceType.MONETARY_BASE:
            # 貨幣基數: 單位億港元，有增長趨勢
            base_value = 18000
            volatility = 200
            trend = np.linspace(0, 1000, len(dates))
        elif source == DataSourceType.GDP_GROWTH:
            # GDP增長率: 圍繞3%波動
            base_value = 3.0
            volatility = 0.8
            trend = np.linspace(-0.5, 0.5, len(dates))
        elif source == DataSourceType.UNEMPLOYMENT_RATE:
            # 失業率: 圍繞3.0%波動
            base_value = 3.0
            volatility = 0.3
            trend = np.linspace(-0.2, 0.2, len(dates))
        else:
            # 默認值
            base_value = 100
            volatility = 5
            trend = np.linspace(0, 0, len(dates))

        # 生成模擬數據
        noise = np.random.normal(0, volatility, len(dates))
        values = base_value + trend + noise

        # 添加一些季節性（對於某些數據源）
        if source in [DataSourceType.GDP_GROWTH, DataSourceType.UNEMPLOYMENT_RATE]:
            seasonal = 0.2 * np.sin(2 * np.pi * np.arange(len(dates)) / 365.25)
            values += seasonal

        # 確保正值
        if source in [DataSourceType.MONETARY_BASE, DataSourceType.HIBOR_OVERNIGHT]:
            values = np.maximum(values, 0.1)
        elif source in [DataSourceType.GDP_GROWTH, DataSourceType.UNEMPLOYMENT_RATE]:
            values = np.maximum(values, 0)

        return pd.Series(values, index=dates, name=source.value)

    def assess_data_quality(self, data: pd.Series) -> QualityMetrics:
        """評估數據質量"""
        if data.empty:
            return QualityMetrics(
                data_points=0,
                completeness=0.0,
                timeliness=0.0,
                consistency=0.0,
                quality_score=0.0,
                missing_values=0,
                outliers=0
            )

        # 基本統計
        total_points = len(data)
        missing_values = data.isna().sum()
        valid_points = total_points - missing_values

        # 完整性分數
        completeness = valid_points / total_points if total_points > 0 else 0.0

        # 時效性分數（基於最新數據的時間）
        latest_date = data.index.max() if not data.empty else None
        timeliness = 1.0
        if latest_date:
            days_old = (datetime.now().date() - latest_date.date()).days
            timeliness = max(0.0, 1.0 - days_old / 30.0)  # 30天內認為新鮮

        # 一致性分數（基於數據的變異係數）
        if valid_points > 1:
            cv = data.std() / data.mean() if data.mean() != 0 else float('inf')
            consistency = max(0.0, 1.0 - cv) if cv < 2 else 0.0
        else:
            consistency = 0.0

        # 異常值檢測（IQR方法）
        outliers = 0
        if valid_points > 4:
            Q1 = data.quantile(0.25)
            Q3 = data.quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            outliers = ((data < lower_bound) | (data > upper_bound)).sum()

        # 異常值比例
        outlier_ratio = outliers / valid_points if valid_points > 0 else 0
        outlier_penalty = min(0.3, outlier_ratio * 0.5)  # 最多扣0.3分

        # 總體質量分數
        quality_score = (completeness * 0.4 + timeliness * 0.2 +
                        consistency * 0.3 + (1 - outlier_penalty) * 0.1)
        quality_score = max(0.0, min(1.0, quality_score))

        return QualityMetrics(
            data_points=total_points,
            completeness=completeness,
            timeliness=timeliness,
            consistency=consistency,
            quality_score=quality_score,
            missing_values=int(missing_values),
            outliers=int(outliers)
        )

    # RSI 計算方法
    async def calculate_rsi(self, request: RSIRequest) -> RSIResponse:
        """計算RSI指標"""
        logger.info(f"Calculating RSI for {request.data_source} with period {request.period}")

        # 獲取數據
        data = await self.fetch_data(request.data_source, request.date_range)
        DataConverter.validate_data_series(data, f"RSI_{request.data_source}")

        # 計算RSI
        rsi_values = self._calculate_rsi_values(data, request.period)

        # 生成信號
        rsi_signals = []
        for i, (date_idx, rsi_val) in enumerate(zip(rsi_values.index, rsi_values.values)):
            if rsi_val >= request.overbought_threshold:
                signal = SignalType.OVERBOUGHT
            elif rsi_val <= request.oversold_threshold:
                signal = SignalType.OVERSOLD
            else:
                signal = SignalType.NEUTRAL

            rsi_signals.append(RSIValue(
                date=date_idx.date(),
                value=round(rsi_val, 2),
                signal=signal
            ))

        # 計算統計信息
        stats = self._calculate_rsi_statistics(rsi_values, request.overbought_threshold, request.oversold_threshold)

        # 評估數據質量
        quality = self.assess_data_quality(data)

        return RSIResponse(
            indicator="RSI",
            data_source=request.data_source,
            period=request.period,
            calculation_time=datetime.now(),
            results=rsi_signals,
            statistics=stats,
            metadata=quality
        )

    def _calculate_rsi_values(self, data: pd.Series, period: int) -> pd.Series:
        """計算RSI值序列"""
        # 計算價格變化
        delta = data.diff()

        # 分離漲跌
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)

        # 計算平均漲跌（使用Wilder平滑方法）
        avg_gain = gain.rolling(window=period, min_periods=1).mean()
        avg_loss = loss.rolling(window=period, min_periods=1).mean()

        # 計算RS和RSI
        rs = avg_gain / avg_loss.replace(0, np.inf)
        rsi = 100 - (100 / (1 + rs))

        return rsi.dropna()

    def _calculate_rsi_statistics(self, rsi_values: pd.Series, overbought: float, oversold: float) -> RSIStatistics:
        """計算RSI統計信息"""
        valid_rsi = rsi_values.dropna()

        if valid_rsi.empty:
            return RSIStatistics(
                mean=0.0,
                std_dev=0.0,
                min_value=0.0,
                max_value=100.0,
                overbought_periods=0,
                oversold_periods=0
            )

        overbought_count = (valid_rsi >= overbought).sum()
        oversold_count = (valid_rsi <= oversold).sum()

        return RSIStatistics(
            mean=float(valid_rsi.mean()),
            std_dev=float(valid_rsi.std()),
            min_value=float(valid_rsi.min()),
            max_value=float(valid_rsi.max()),
            overbought_periods=int(overbought_count),
            oversold_periods=int(oversold_count)
        )

    # MACD 計算方法
    async def calculate_macd(self, request: MACDRequest) -> MACDResponse:
        """計算MACD指標"""
        logger.info(f"Calculating MACD for {request.data_source}")

        # 獲取數據
        data = await self.fetch_data(request.data_source, request.date_range)
        DataConverter.validate_data_series(data, f"MACD_{request.data_source}")

        # 計算MACD
        macd_data = self._calculate_macd_values(
            data, request.fast_period, request.slow_period, request.signal_period
        )

        # 生成信號
        macd_signals = []
        for i, (date_idx, row) in enumerate(macd_data.iterrows()):
            # 檢測交叉信號
            if i > 0:
                prev_macd = macd_data.iloc[i-1]['macd_line']
                prev_signal = macd_data.iloc[i-1]['signal_line']
                curr_macd = row['macd_line']
                curr_signal = row['signal_line']

                if prev_macd <= prev_signal and curr_macd > curr_signal:
                    signal = SignalType.BULLISH_CROSSOVER
                elif prev_macd >= prev_signal and curr_macd < curr_signal:
                    signal = SignalType.BEARISH_CROSSOVER
                else:
                    signal = SignalType.NEUTRAL
            else:
                signal = SignalType.NEUTRAL

            macd_signals.append(MACDValue(
                date=date_idx.date(),
                macd_line=round(row['macd_line'], 4),
                signal_line=round(row['signal_line'], 4),
                histogram=round(row['histogram'], 4),
                signal=signal
            ))

        # 計算信號統計
        signal_stats = self._calculate_macd_signals(macd_data)

        # 評估數據質量
        quality = self.assess_data_quality(data)

        return MACDResponse(
            indicator="MACD",
            data_source=request.data_source,
            parameters={
                "fast_period": request.fast_period,
                "slow_period": request.slow_period,
                "signal_period": request.signal_period
            },
            calculation_time=datetime.now(),
            results=macd_signals,
            signals=signal_stats,
            metadata=quality
        )

    def _calculate_macd_values(self, data: pd.Series, fast: int, slow: int, signal: int) -> pd.DataFrame:
        """計算MACD值"""
        # 計算EMA
        ema_fast = data.ewm(span=fast).mean()
        ema_slow = data.ewm(span=slow).mean()

        # MACD線
        macd_line = ema_fast - ema_slow

        # 信號線
        signal_line = macd_line.ewm(span=signal).mean()

        # 柱狀圖
        histogram = macd_line - signal_line

        return pd.DataFrame({
            'macd_line': macd_line,
            'signal_line': signal_line,
            'histogram': histogram
        }).dropna()

    def _calculate_macd_signals(self, macd_data: pd.DataFrame) -> MACDSignals:
        """計算MACD信號統計"""
        if len(macd_data) < 2:
            return MACDSignals(
                bullish_crossovers=0,
                bearish_crossovers=0,
                divergences=0
            )

        # 檢測交叉
        macd_line = macd_data['macd_line']
        signal_line = macd_data['signal_line']

        # 金叉（MACD線向上穿過信號線）
        golden_cross = ((macd_line.shift(1) <= signal_line.shift(1)) &
                       (macd_line > signal_line)).sum()

        # 死叉（MACD線向下穿過信號線）
        death_cross = ((macd_line.shift(1) >= signal_line.shift(1)) &
                      (macd_line < signal_line)).sum()

        return MACDSignals(
            bullish_crossovers=int(golden_cross),
            bearish_crossovers=int(death_cross),
            divergences=0  # 簡化版本，實際需要更複雜的背離檢測
        )

    # Bollinger Bands 計算方法
    async def calculate_bollinger_bands(self, request: BollingerBandsRequest) -> BollingerBandsResponse:
        """計算Bollinger Bands"""
        logger.info(f"Calculating Bollinger Bands for {request.data_source}")

        # 獲取數據
        data = await self.fetch_data(request.data_source, request.date_range)
        DataConverter.validate_data_series(data, f"BB_{request.data_source}")

        # 計算Bollinger Bands
        bb_data = self._calculate_bollinger_bands_values(data, request.period, request.std_dev_multiplier)

        # 生成信號和分析
        bb_signals = []
        squeeze_count = 0
        breakout_count = 0
        above_upper = 0
        below_lower = 0

        for i, (date_idx, row) in enumerate(bb_data.iterrows()):
            current_value = data.loc[date_idx]

            # 判斷位置
            if current_value >= row['upper_band']:
                position = "above_upper"
                above_upper += 1
                breakout_count += 1
                breakout = True
            elif current_value <= row['lower_band']:
                position = "below_lower"
                below_lower += 1
                breakout_count += 1
                breakout = True
            else:
                position = "within_bands"
                breakout = False

            # 檢測擠壓
            width = row['upper_band'] - row['lower_band']
            avg_width = bb_data['upper_band'] - bb_data['lower_band']
            squeeze = width < (avg_width.mean() * 0.8)  # 寬度小於平均80%視為擠壓
            if squeeze:
                squeeze_count += 1

            bb_signals.append(BollingerBandsValue(
                date=date_idx.date(),
                upper_band=round(row['upper_band'], 4),
                middle_band=round(row['middle_band'], 4),
                lower_band=round(row['lower_band'], 4),
                current_value=round(current_value, 4),
                position=position,
                width=round(width, 4),
                squeeze=squeeze,
                breakout=breakout
            ))

        # 計算分析信息
        analysis = self._calculate_bollinger_bands_analysis(bb_data, squeeze_count, breakout_count, above_upper, below_lower)

        # 評估數據質量
        quality = self.assess_data_quality(data)

        return BollingerBandsResponse(
            indicator="BollingerBands",
            data_source=request.data_source,
            period=request.period,
            std_dev_multiplier=request.std_dev_multiplier,
            calculation_time=datetime.now(),
            results=bb_signals,
            analysis=analysis,
            metadata=quality
        )

    def _calculate_bollinger_bands_values(self, data: pd.Series, period: int, std_dev: float) -> pd.DataFrame:
        """計算Bollinger Bands值"""
        # 計算中軌（SMA）
        middle_band = data.rolling(window=period).mean()

        # 計算標準差
        rolling_std = data.rolling(window=period).std()

        # 計算上下軌
        upper_band = middle_band + (rolling_std * std_dev)
        lower_band = middle_band - (rolling_std * std_dev)

        return pd.DataFrame({
            'upper_band': upper_band,
            'middle_band': middle_band,
            'lower_band': lower_band
        }).dropna()

    def _calculate_bollinger_bands_analysis(self, bb_data: pd.DataFrame, squeeze_count: int,
                                         breakout_count: int, above_upper: int, below_lower: int) -> BollingerBandsAnalysis:
        """計算Bollinger Bands分析"""
        if bb_data.empty:
            return BollingerBandsAnalysis(
                average_width=0.0,
                squeeze_periods=0,
                breakout_periods=0,
                above_upper=0,
                below_lower=0
            )

        # 計算平均寬度
        width = bb_data['upper_band'] - bb_data['lower_band']
        avg_width = float(width.mean())

        return BollingerBandsAnalysis(
            average_width=avg_width,
            squeeze_periods=squeeze_count,
            breakout_periods=breakout_count,
            above_upper=above_upper,
            below_lower=below_lower
        )

    # 批量處理方法
    async def calculate_batch(self, request: BatchRequest) -> Dict[str, Any]:
        """批量計算多個指標"""
        logger.info(f"Calculating batch indicators for {request.data_source}")
        start_time = datetime.now()

        results = {}

        # 並行處理多個指標
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {}

            for indicator_config in request.indicators:
                if indicator_config.type == IndicatorType.RSI:
                    rsi_request = RSIRequest(
                        data_source=request.data_source,
                        period=indicator_config.parameters.get('period', 14),
                        overbought_threshold=indicator_config.parameters.get('overbought_threshold', 70),
                        oversold_threshold=indicator_config.parameters.get('oversold_threshold', 30),
                        date_range=request.date_range
                    )
                    futures['RSI'] = executor.submit(asyncio.run, self.calculate_rsi(rsi_request))

                elif indicator_config.type == IndicatorType.MACD:
                    macd_request = MACDRequest(
                        data_source=request.data_source,
                        fast_period=indicator_config.parameters.get('fast_period', 12),
                        slow_period=indicator_config.parameters.get('slow_period', 26),
                        signal_period=indicator_config.parameters.get('signal_period', 9),
                        date_range=request.date_range
                    )
                    futures['MACD'] = executor.submit(asyncio.run, self.calculate_macd(macd_request))

                elif indicator_config.type == IndicatorType.BOLLINGER_BANDS:
                    bb_request = BollingerBandsRequest(
                        data_source=request.data_source,
                        period=indicator_config.parameters.get('period', 20),
                        std_dev_multiplier=indicator_config.parameters.get('std_dev_multiplier', 2.0),
                        date_range=request.date_range
                    )
                    futures['BollingerBands'] = executor.submit(asyncio.run, self.calculate_bollinger_bands(bb_request))

            # 等待所有任務完成
            for indicator_name, future in futures.items():
                try:
                    result = future.result()
                    results[indicator_name] = result
                except Exception as e:
                    logger.error(f"Error calculating {indicator_name}: {e}")
                    results[indicator_name] = {"error": str(e)}

        processing_time = (datetime.now() - start_time).total_seconds()

        # 生成摘要
        summary = {
            "total_indicators": len(request.indicators),
            "successful_calculations": len([r for r in results.values() if "error" not in r]),
            "failed_calculations": len([r for r in results.values() if "error" in r]),
            "data_source": request.data_source.value,
            "date_range": f"{request.date_range.start_date} to {request.date_range.end_date}"
        }

        return {
            "data_source": request.data_source,
            "calculation_time": datetime.now(),
            "processing_time_seconds": processing_time,
            "results": results,
            "summary": summary
        }


class NonPriceDataProcessor:
    """非價格數據處理器"""

    def __init__(self):
        self.supported_sources = [
            DataSourceType.HIBOR_OVERNIGHT,
            DataSourceType.MONETARY_BASE,
            DataSourceType.GDP_GROWTH,
            DataSourceType.UNEMPLOYMENT_RATE,
            DataSourceType.PROPERTY_PRICE,
            DataSourceType.RETAIL_SALES,
            DataSourceType.VISITOR_ARRIVALS,
            DataSourceType.TRADE_VOLUME
        ]

        self.source_descriptions = {
            DataSourceType.HIBOR_OVERNIGHT: "HIBOR隔夜利率",
            DataSourceType.MONETARY_BASE: "香港貨幣基數",
            DataSourceType.GDP_GROWTH: "GDP增長率",
            DataSourceType.UNEMPLOYMENT_RATE: "失業率",
            DataSourceType.PROPERTY_PRICE: "物業價格指數",
            DataSourceType.RETAIL_SALES: "零售銷售額",
            DataSourceType.VISITOR_ARRIVALS: "訪港旅客數量",
            DataSourceType.TRADE_VOLUME: "貿易總量"
        }

    def get_available_sources(self) -> List[Dict[str, Any]]:
        """獲取可用數據源信息"""
        sources = []

        for source in self.supported_sources:
            sources.append({
                "name": source.value,
                "description": self.source_descriptions.get(source, "未知數據源"),
                "data_type": self._get_data_type(source),
                "frequency": self._get_frequency(source),
                "supported_indicators": self._get_supported_indicators(source)
            })

        return sources

    def _get_data_type(self, source: DataSourceType) -> str:
        """獲取數據類型"""
        if "rate" in source.value:
            return "利率"
        elif source in [DataSourceType.MONETARY_BASE, DataSourceType.RETAIL_SALES, DataSourceType.TRADE_VOLUME]:
            return "金額"
        elif "growth" in source.value or source == DataSourceType.UNEMPLOYMENT_RATE:
            return "百分比"
        else:
            return "指數"

    def _get_frequency(self, source: DataSourceType) -> str:
        """獲取更新頻率"""
        if source in [DataSourceType.HIBOR_OVERNIGHT]:
            return "每日"
        elif source in [DataSourceType.MONETARY_BASE, DataSourceType.UNEMPLOYMENT_RATE]:
            return "每月"
        elif source == DataSourceType.GDP_GROWTH:
            return "每季"
        else:
            return "不定期"

    def _get_supported_indicators(self, source: DataSourceType) -> List[str]:
        """獲取支持的指標"""
        # 所有數據源都支持基礎指標
        base_indicators = ["RSI", "MACD", "BollingerBands"]

        # 根據數據特性添加特定指標
        if "rate" in source.value:
            base_indicators.extend(["Stochastic", "WilliamsR"])

        return base_indicators


class ResponseFormatter:
    """響應格式化器"""

    @staticmethod
    def format_error_response(error_type: str, message: str, **kwargs) -> Dict[str, Any]:
        """格式化錯誤響應"""
        response = {
            "error": error_type,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }

        # 添加可選字段
        for key, value in kwargs.items():
            if value is not None:
                response[key] = value

        return response

    @staticmethod
    def format_success_response(data: Any, meta: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """格式化成功響應"""
        response = {
            "success": True,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }

        if meta:
            response["metadata"] = meta

        return response
