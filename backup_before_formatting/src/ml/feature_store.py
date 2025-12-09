"""
高級特徵存儲系統
生產級別的實時特徵工程和數據版本管理

功能:
- 實時特徵計算和存儲
- 特徵版本控制和數據血緣追蹤
- 高頻特徵更新和緩存
- 多時間框架特徵支持
- 特徵質量監控和異常檢測
"""

import asyncio
import hashlib
import json
import logging
import pickle
import sqlite3
from collections import defaultdict
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np
import pandas as pd
import redis

try:
    import feast
    from feast import Entity, FeatureStore, FeatureView
    from feast.data_source import PushSource
    from feast.types import Float32, Int64, String

    FEAST_AVAILABLE = True
except ImportError:
    FEAST_AVAILABLE = False

try:
    import dvc.api

    DVC_AVAILABLE = True
except ImportError:
    DVC_AVAILABLE = False

from sklearn.decomposition import PCA
from sklearn.feature_selection import SelectKBest, f_regression
from sklearn.preprocessing import MinMaxScaler, RobustScaler, StandardScaler


class FeatureType(Enum):
    """特徵類型"""

    PRICE = "price"  # 價格相關特徵
    VOLUME = "volume"  # 成交量相關特徵
    TECHNICAL = "technical"  # 技術指標特徵
    SENTIMENT = "sentiment"  # 情緒特徵
    MACRO = "macro"  # 宏觀經濟特徵
    ALTERNATIVE = "alternative"  # 替代數據特徵
    DERIVED = "derived"  # 衍生特徵
    REALTIME = "realtime"  # 實時特徵


class TimeFrame(Enum):
    """時間框架"""

    TICK = "tick"
    MINUTE_1 = "1m"
    MINUTE_5 = "5m"
    MINUTE_15 = "15m"
    MINUTE_30 = "30m"
    HOUR_1 = "1h"
    HOUR_4 = "4h"
    DAY_1 = "1d"
    WEEK_1 = "1w"
    MONTH_1 = "1M"


@dataclass
class FeatureMetadata:
    """特徵元數據"""

    name: str
    feature_type: FeatureType
    timeframe: TimeFrame
    description: str
    computation_logic: str
    dependencies: Set[str] = field(default_factory=set)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    version: str = "1.0"
    is_active: bool = True
    quality_score: float = 1.0
    last_computed: Optional[datetime] = None
    compute_frequency: timedelta = field(default_factory=lambda: timedelta(minutes=5))
    data_source: str = "default"
    tags: List[str] = field(default_factory=list)
    owner: str = "system"


@dataclass
class FeatureValue:
    """特徵值"""

    symbol: str
    timestamp: datetime
    feature_name: str
    value: float
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class FeatureRegistry:
    """特徵註冊中心"""

    def __init__(self):
        self.features: Dict[str, FeatureMetadata] = {}
        self.feature_dependencies: Dict[str, Set[str]] = defaultdict(set)
        self.dependents: Dict[str, Set[str]] = defaultdict(set)

    def register_feature(self, metadata: FeatureMetadata) -> bool:
        """註冊特徵"""
        try:
            # 檢查特徵名稱唯一性
            if metadata.name in self.features:
                logging.warning(f"Feature {metadata.name} already exists, updating...")

            # 驗證依賴關係
            for dep in metadata.dependencies:
                if dep not in self.features:
                    raise ValueError(
                        f"Dependency {dep} not found for feature {metadata.name}"
                    )

            # 更新依賴關係
            old_deps = self.feature_dependencies.get(metadata.name, set())
            for dep in old_deps:
                self.dependents[dep].discard(metadata.name)

            for dep in metadata.dependencies:
                self.dependents[dep].add(metadata.name)

            self.feature_dependencies[metadata.name] = metadata.dependencies.copy()
            metadata.updated_at = datetime.now()
            self.features[metadata.name] = metadata

            logging.info(f"Feature {metadata.name} registered successfully")
            return True

        except Exception as e:
            logging.error(f"Failed to register feature {metadata.name}: {str(e)}")
            return False

    def get_feature(self, name: str) -> Optional[FeatureMetadata]:
        """獲取特徵元數據"""
        return self.features.get(name)

    def get_features_by_type(self, feature_type: FeatureType) -> List[FeatureMetadata]:
        """根據類型獲取特徵列表"""
        return [f for f in self.features.values() if f.feature_type == feature_type]

    def get_feature_dependencies(
        self, feature_name: str, recursive: bool = False
    ) -> Set[str]:
        """獲取特徵依賴"""
        if not recursive:
            return self.feature_dependencies.get(feature_name, set()).copy()

        dependencies = set()
        queue = [feature_name]
        visited = set()

        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)

            deps = self.feature_dependencies.get(current, set())
            for dep in deps:
                if dep not in visited:
                    dependencies.add(dep)
                    queue.append(dep)

        return dependencies

    def validate_feature_graph(self) -> List[str]:
        """驗證特徵圖，檢查循環依賴"""
        errors = []

        def detect_cycle(node: str, visited: Set[str], rec_stack: Set[str]) -> bool:
            visited.add(node)
            rec_stack.add(node)

            for neighbor in self.feature_dependencies.get(node, set()):
                if neighbor not in visited:
                    if detect_cycle(neighbor, visited, rec_stack):
                        return True
                elif neighbor in rec_stack:
                    return True

            rec_stack.remove(node)
            return False

        visited = set()
        for feature_name in self.features:
            if feature_name not in visited:
                if detect_cycle(feature_name, visited, set()):
                    errors.append(
                        f"Circular dependency detected for feature {feature_name}"
                    )

        return errors


class FeatureCalculator:
    """特徵計算器"""

    def __init__(self):
        self.logger = logging.getLogger("hk_quant_system.feature_calculator")
        self.scalers: Dict[str, Any] = {}
        self.pca_models: Dict[str, PCA] = {}

    def calculate_price_features(
        self, df: pd.DataFrame, window_sizes: List[int] = [5, 10, 20, 60]
    ) -> pd.DataFrame:
        """計算價格相關特徵"""
        features = pd.DataFrame(index=df.index)

        for window in window_sizes:
            # 移動平均
            features[f"sma_{window}"] = df["close"].rolling(window).mean()
            features[f"ema_{window}"] = df["close"].ewm(span=window).mean()

            # 價格相對位置
            features[f"price_position_{window}"] = (
                df["close"] - df["close"].rolling(window).min()
            ) / (df["close"].rolling(window).max() - df["close"].rolling(window).min())

            # 價格動量
            features[f"momentum_{window}"] = df["close"] / df["close"].shift(window) - 1

            # 波動率
            features[f"volatility_{window}"] = (
                df["close"].rolling(window).std() / df["close"].rolling(window).mean()
            )

            # 最高最低價位置
            features[f"high_position_{window}"] = (
                df["high"] - df["close"].rolling(window).min()
            ) / (df["close"].rolling(window).max() - df["close"].rolling(window).min())

            features[f"low_position_{window}"] = (
                df["low"] - df["close"].rolling(window).min()
            ) / (df["close"].rolling(window).max() - df["close"].rolling(window).min())

        return features

    def calculate_volume_features(
        self, df: pd.DataFrame, window_sizes: List[int] = [5, 10, 20]
    ) -> pd.DataFrame:
        """計算成交量特徵"""
        features = pd.DataFrame(index=df.index)

        for window in window_sizes:
            # 成交量移動平均
            features[f"volume_sma_{window}"] = df["volume"].rolling(window).mean()
            features[f"volume_ema_{window}"] = df["volume"].ewm(span=window).mean()

            # 成交量相對位置
            features[f"volume_position_{window}"] = (
                df["volume"] - df["volume"].rolling(window).min()
            ) / (
                df["volume"].rolling(window).max()
                - df["volume"].rolling(window).min()
                + 1e-8
            )

            # 價量關係
            features[f"price_volume_corr_{window}"] = (
                df["close"].rolling(window).corr(df["volume"])
            )

            # 成交量變化率
            features[f"volume_change_{window}"] = (
                df["volume"] / df["volume"].shift(window) - 1
            )

            # VWAP (簡化版)
            features[f"vwap_{window}"] = (df["close"] * df["volume"]).rolling(
                window
            ).sum() / df["volume"].rolling(window).sum()

        return features

    def calculate_technical_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """計算技術指標特徵"""
        features = pd.DataFrame(index=df.index)

        # RSI
        delta = df["close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / (loss + 1e-8)
        features["rsi"] = 100 - (100 / (1 + rs))

        # MACD
        ema_12 = df["close"].ewm(span=12).mean()
        ema_26 = df["close"].ewm(span=26).mean()
        features["macd"] = ema_12 - ema_26
        features["macd_signal"] = features["macd"].ewm(span=9).mean()
        features["macd_histogram"] = features["macd"] - features["macd_signal"]

        # 布林帶
        bb_middle = df["close"].rolling(20).mean()
        bb_std = df["close"].rolling(20).std()
        features["bb_upper"] = bb_middle + (bb_std * 2)
        features["bb_lower"] = bb_middle - (bb_std * 2)
        features["bb_position"] = (df["close"] - features["bb_lower"]) / (
            features["bb_upper"] - features["bb_lower"]
        )
        features["bb_width"] = (features["bb_upper"] - features["bb_lower"]) / bb_middle

        # ATR
        high_low = df["high"] - df["low"]
        high_close = np.abs(df["high"] - df["close"].shift())
        low_close = np.abs(df["low"] - df["close"].shift())
        true_range = np.maximum(high_low, np.maximum(high_close, low_close))
        features["atr"] = true_range.rolling(14).mean()
        features["atr_ratio"] = features["atr"] / df["close"]

        # 隨機指標
        low_14 = df["low"].rolling(14).min()
        high_14 = df["high"].rolling(14).max()
        features["stochastic_k"] = 100 * (
            (df["close"] - low_14) / (high_14 - low_14 + 1e-8)
        )
        features["stochastic_d"] = features["stochastic_k"].rolling(3).mean()

        # ADX
        features["adx"] = self._calculate_adx(df)

        # OBV
        features["obv"] = (np.sign(df["close"].diff()) * df["volume"]).cumsum()
        features["obv_sma"] = features["obv"].rolling(20).mean()

        # MFI
        typical_price = (df["high"] + df["low"] + df["close"]) / 3
        money_flow = typical_price * df["volume"]
        positive_flow = money_flow.where(typical_price > typical_price.shift(1), 0)
        negative_flow = money_flow.where(typical_price < typical_price.shift(1), 0)

        positive_mf = positive_flow.rolling(14).sum()
        negative_mf = negative_flow.rolling(14).sum()

        mfi_ratio = positive_mf / (negative_mf + 1e-8)
        features["mfi"] = 100 - (100 / (1 + mfi_ratio))

        return features

    def _calculate_adx(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """計算ADX指標"""
        high_diff = df["high"].diff()
        low_diff = df["low"].diff()

        plus_dm = np.where((high_diff > low_diff) & (high_diff > 0), high_diff, 0)

        minus_dm = np.where((low_diff > high_diff) & (low_diff > 0), low_diff, 0)

        tr = np.maximum(
            df["high"] - df["low"],
            np.maximum(
                np.abs(df["high"] - df["close"].shift()),
                np.abs(df["low"] - df["close"].shift()),
            ),
        )

        plus_dm = pd.Series(plus_dm, index=df.index).rolling(period).mean()
        minus_dm = pd.Series(minus_dm, index=df.index).rolling(period).mean()
        tr = pd.Series(tr, index=df.index).rolling(period).mean()

        plus_di = 100 * (plus_dm / (tr + 1e-8))
        minus_di = 100 * (minus_dm / (tr + 1e-8))

        dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di + 1e-8)
        adx = dx.rolling(period).mean()

        return adx

    def calculate_sentiment_features(
        self, sentiment_data: pd.DataFrame
    ) -> pd.DataFrame:
        """計算情緒特徵"""
        if sentiment_data.empty:
            return pd.DataFrame()

        features = pd.DataFrame(index=sentiment_data.index)

        # 情緒分數
        if "sentiment_score" in sentiment_data.columns:
            features["sentiment_score"] = sentiment_data["sentiment_score"]
            features["sentiment_ma_5"] = (
                sentiment_data["sentiment_score"].rolling(5).mean()
            )
            features["sentiment_ma_20"] = (
                sentiment_data["sentiment_score"].rolling(20).mean()
            )

            # 情緒變化
            features["sentiment_change"] = sentiment_data["sentiment_score"].diff()
            features["sentiment_volatility"] = (
                sentiment_data["sentiment_score"].rolling(10).std()
            )

        # 新聞數量
        if "news_count" in sentiment_data.columns:
            features["news_count"] = sentiment_data["news_count"]
            features["news_count_ma"] = sentiment_data["news_count"].rolling(5).mean()

        return features

    def calculate_macro_features(self, macro_data: pd.DataFrame) -> pd.DataFrame:
        """計算宏觀經濟特徵"""
        if macro_data.empty:
            return pd.DataFrame()

        features = pd.DataFrame(index=macro_data.index)

        # 利率相關
        if "interest_rate" in macro_data.columns:
            features["interest_rate"] = macro_data["interest_rate"]
            features["interest_rate_change"] = macro_data["interest_rate"].diff()

        # 匯率相關
        if "usd_hkd" in macro_data.columns:
            features["usd_hkd"] = macro_data["usd_hkd"]
            features["usd_hkd_change"] = macro_data["usd_hkd"].pct_change()

        # 市場情緒指數
        if "vix" in macro_data.columns:
            features["vix"] = macro_data["vix"]
            features["vix_ma"] = macro_data["vix"].rolling(20).mean()

        return features


class AdvancedFeatureStore:
    """
    高級特徵存儲系統

    整合特徵註冊、計算、存儲和服務的完整解決方案
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        db_path: str = "feature_store.db",
        cache_dir: str = "feature_cache",
        enable_feast: bool = False,
    ):
        self.logger = logging.getLogger("hk_quant_system.feature_store")

        # 初始化組件
        self.registry = FeatureRegistry()
        self.calculator = FeatureCalculator()

        # Redis連接 (用於緩存)
        try:
            self.redis_client = redis.from_url(redis_url)
            self.redis_client.ping()
        except Exception as e:
            self.logger.warning(f"Redis connection failed: {e}")
            self.redis_client = None

        # SQLite數據庫 (用於元數據和持久化)
        self.db_path = db_path
        self._init_database()

        # 緩存目錄
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)

        # 特徵數據緩存
        self.feature_cache: Dict[str, pd.DataFrame] = {}
        self.cache_expiry = timedelta(minutes=5)

        # 初始化Feast (如果可用)
        self.feast_store = None
        if enable_feast and FEAST_AVAILABLE:
            self._init_feast()

        # 特徵質量監控
        self.quality_monitor = FeatureQualityMonitor()

        # 初始化默認特徵
        self._register_default_features()

        # 實時特徵更新任務
        self._update_tasks: Set[asyncio.Task] = set()

    def _init_database(self):
        """初始化SQLite數據庫"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS feature_metadata (
                name TEXT PRIMARY KEY,
                feature_type TEXT,
                timeframe TEXT,
                description TEXT,
                dependencies TEXT,
                created_at TEXT,
                updated_at TEXT,
                version TEXT,
                is_active BOOLEAN,
                quality_score REAL,
                last_computed TEXT,
                compute_frequency INTEGER,
                data_source TEXT,
                tags TEXT,
                owner TEXT
            )
        """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS feature_values (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT,
                timestamp TEXT,
                feature_name TEXT,
                value REAL,
                confidence REAL,
                metadata TEXT,
                UNIQUE(symbol, timestamp, feature_name)
            )
        """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_feature_values_symbol
            ON feature_values(symbol)
        """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_feature_values_timestamp
            ON feature_values(timestamp)
        """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_feature_values_feature
            ON feature_values(feature_name)
        """
        )

        conn.commit()
        conn.close()

    def _init_feast(self):
        """初始化Feast特徵存儲"""
        try:
            # 這裡可以創建Feast配置並初始化FeatureStore
            # self.feast_store = FeatureStore(repo_path="feast_repo")
            self.logger.info("Feast feature store initialized")
        except Exception as e:
            self.logger.warning(f"Feast initialization failed: {e}")

    def _register_default_features(self):
        """註冊默認特徵"""
        default_features = [
            # 價格特徵
            FeatureMetadata(
                name="sma_5",
                feature_type=FeatureType.PRICE,
                timeframe=TimeFrame.DAY_1,
                description="5日簡單移動平均",
                computation_logic="close.rolling(5).mean()",
            ),
            FeatureMetadata(
                name="sma_20",
                feature_type=FeatureType.PRICE,
                timeframe=TimeFrame.DAY_1,
                description="20日簡單移動平均",
                computation_logic="close.rolling(20).mean()",
            ),
            FeatureMetadata(
                name="price_position_20",
                feature_type=FeatureType.PRICE,
                timeframe=TimeFrame.DAY_1,
                description="價格在20日區間中的相對位置",
                computation_logic="(close - close.rolling(20).min()) / (close.rolling(20).max() - close.rolling(20).min())",
            ),
            # 技術指標特徵
            FeatureMetadata(
                name="rsi",
                feature_type=FeatureType.TECHNICAL,
                timeframe=TimeFrame.DAY_1,
                description="相對強弱指標",
                computation_logic="calculate_rsi(close, 14)",
            ),
            FeatureMetadata(
                name="macd",
                feature_type=FeatureType.TECHNICAL,
                timeframe=TimeFrame.DAY_1,
                description="MACD指標",
                computation_logic="calculate_macd(close)",
            ),
            FeatureMetadata(
                name="bb_position",
                feature_type=FeatureType.TECHNICAL,
                timeframe=TimeFrame.DAY_1,
                description="布林帶位置",
                computation_logic="calculate_bollinger_position(close)",
            ),
            FeatureMetadata(
                name="atr_ratio",
                feature_type=FeatureType.TECHNICAL,
                timeframe=TimeFrame.DAY_1,
                description="ATR相對比率",
                computation_logic="atr / close",
            ),
            # 成交量特徵
            FeatureMetadata(
                name="volume_position_20",
                feature_type=FeatureType.VOLUME,
                timeframe=TimeFrame.DAY_1,
                description="成交量在20日區間中的相對位置",
                computation_logic="(volume - volume.rolling(20).min()) / (volume.rolling(20).max() - volume.rolling(20).min())",
            ),
            FeatureMetadata(
                name="price_volume_corr_20",
                feature_type=FeatureType.VOLUME,
                timeframe=TimeFrame.DAY_1,
                description="價量相關性",
                computation_logic="close.rolling(20).corr(volume)",
            ),
        ]

        for feature in default_features:
            self.registry.register_feature(feature)

    async def compute_features(
        self,
        symbol: str,
        data: pd.DataFrame,
        feature_types: Optional[List[FeatureType]] = None,
    ) -> pd.DataFrame:
        """
        計算指定股票的所有特徵

        Args:
            symbol: 股票代碼
            data: OHLCV數據
            feature_types: 要計算的特徵類型列表

        Returns:
            包含所有計算特徵的DataFrame
        """
        try:
            self.logger.info(f"Computing features for {symbol}")

            if feature_types is None:
                feature_types = [
                    FeatureType.PRICE,
                    FeatureType.VOLUME,
                    FeatureType.TECHNICAL,
                ]

            all_features = pd.DataFrame(index=data.index)

            # 計算各類特徵
            if FeatureType.PRICE in feature_types:
                price_features = self.calculator.calculate_price_features(data)
                all_features = pd.concat([all_features, price_features], axis=1)

            if FeatureType.VOLUME in feature_types:
                volume_features = self.calculator.calculate_volume_features(data)
                all_features = pd.concat([all_features, volume_features], axis=1)

            if FeatureType.TECHNICAL in feature_types:
                technical_features = self.calculator.calculate_technical_features(data)
                all_features = pd.concat([all_features, technical_features], axis=1)

            # 特徵質量檢查
            quality_report = self.quality_monitor.check_features(all_features)
            if quality_report["overall_quality"] < 0.8:
                self.logger.warning(
                    f"Low feature quality for {symbol}: {quality_report}"
                )

            # 緩存特徵
            cache_key = f"{symbol}_{datetime.now().strftime('%Y-%m-%d')}"
            self.feature_cache[cache_key] = all_features

            # 異步保存到數據庫
            asyncio.create_task(self._save_features_to_db(symbol, all_features))

            return all_features

        except Exception as e:
            self.logger.error(f"Feature computation failed for {symbol}: {str(e)}")
            raise

    async def get_features(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        feature_names: Optional[List[str]] = None,
    ) -> pd.DataFrame:
        """
        獲取指定時間範圍的特徵數據

        Args:
            symbol: 股票代碼
            start_date: 開始日期
            end_date: 結束日期
            feature_names: 特徵名稱列表

        Returns:
            特徵數據DataFrame
        """
        try:
            # 首先檢查緩存
            cache_key = f"{symbol}_{start_date.strftime('%Y-%m-%d')}"
            if cache_key in self.feature_cache:
                cached_data = self.feature_cache[cache_key]
                if feature_names:
                    cached_data = cached_data[feature_names]
                return cached_data

            # 從數據庫加載
            conn = sqlite3.connect(self.db_path)

            query = """
                SELECT timestamp, feature_name, value, confidence
                FROM feature_values
                WHERE symbol = ? AND timestamp BETWEEN ? AND ?
            """
            params = [symbol, start_date.isoformat(), end_date.isoformat()]

            if feature_names:
                placeholders = ",".join(["?" for _ in feature_names])
                query += f" AND feature_name IN ({placeholders})"
                params.extend(feature_names)

            query += " ORDER BY timestamp"

            df = pd.read_sql_query(query, conn, params=params)
            conn.close()

            if df.empty:
                return pd.DataFrame()

            # 轉換為寬格式
            features_df = df.pivot(
                index="timestamp", columns="feature_name", values="value"
            )

            # 添加置信度信息
            confidence_df = df.pivot(
                index="timestamp", columns="feature_name", values="confidence"
            )

            # 轉換時間戳
            features_df.index = pd.to_datetime(features_df.index)

            return features_df

        except Exception as e:
            self.logger.error(f"Failed to get features for {symbol}: {str(e)}")
            return pd.DataFrame()

    async def update_realtime_features(self, symbol: str, current_data: pd.DataFrame):
        """更新實時特徵"""
        try:
            # 計算實時特徵
            realtime_features = await self.compute_features(
                symbol, current_data, [FeatureType.REALTIME]
            )

            # 異步更新緩存和數據庫
            cache_key = f"{symbol}_realtime"
            self.feature_cache[cache_key] = realtime_features.tail(
                100
            )  # 保留最近100個數據點

            await self._save_features_to_db(symbol, realtime_features.tail(1))

            self.logger.info(f"Realtime features updated for {symbol}")

        except Exception as e:
            self.logger.error(f"Realtime feature update failed for {symbol}: {str(e)}")

    async def _save_features_to_db(self, symbol: str, features: pd.DataFrame):
        """保存特徵到數據庫"""
        try:
            conn = sqlite3.connect(self.db_path)

            # 準備數據
            records = []
            for timestamp, row in features.iterrows():
                for feature_name, value in row.items():
                    if pd.notna(value):
                        records.append(
                            (
                                symbol,
                                timestamp.isoformat(),
                                feature_name,
                                float(value),
                                1.0,  # 默認置信度
                                json.dumps({}),
                            )
                        )

            # 批量插入
            cursor = conn.cursor()
            cursor.executemany(
                """
                INSERT OR REPLACE INTO feature_values
                (symbol, timestamp, feature_name, value, confidence, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                records,
            )

            conn.commit()
            conn.close()

            self.logger.info(f"Saved {len(records)} feature values to database")

        except Exception as e:
            self.logger.error(f"Failed to save features to database: {str(e)}")

    async def batch_compute_features(
        self, symbols: List[str], data_dict: Dict[str, pd.DataFrame]
    ) -> Dict[str, pd.DataFrame]:
        """批量計算特徵"""
        self.logger.info(
            f"Starting batch feature computation for {len(symbols)} symbols"
        )

        results = {}
        tasks = []

        for symbol in symbols:
            if symbol in data_dict:
                task = asyncio.create_task(
                    self.compute_features(symbol, data_dict[symbol])
                )
                tasks.append((symbol, task))

        # 等待所有任務完成
        for symbol, task in tasks:
            try:
                results[symbol] = await task
            except Exception as e:
                self.logger.error(f"Batch computation failed for {symbol}: {str(e)}")
                results[symbol] = pd.DataFrame()

        success_count = sum(1 for df in results.values() if not df.empty)
        self.logger.info(
            f"Batch computation completed: {success_count}/{len(symbols)} successful"
        )

        return results

    def get_feature_importance(
        self, symbol: str, feature_names: List[str], target: pd.Series
    ) -> Dict[str, float]:
        """計算特徵重要性"""
        try:
            # 獲取特徵數據
            end_date = datetime.now()
            start_date = end_date - timedelta(days=90)

            features_df = asyncio.run(
                self.get_features(symbol, start_date, end_date, feature_names)
            )

            if features_df.empty:
                return {}

            # 使用SelectKBest計算特徵重要性
            selector = SelectKBest(score_func=f_regression, k="all")
            selector.fit(features_df, target)

            importance_dict = dict(zip(feature_names, selector.scores_))

            # 正規化重要性分數
            total_score = sum(importance_dict.values())
            if total_score > 0:
                importance_dict = {
                    k: v / total_score for k, v in importance_dict.items()
                }

            return importance_dict

        except Exception as e:
            self.logger.error(f"Feature importance calculation failed: {str(e)}")
            return {}

    def clear_cache(self):
        """清除緩存"""
        self.feature_cache.clear()
        if self.redis_client:
            self.redis_client.flushdb()
        self.logger.info("Feature cache cleared")


class FeatureQualityMonitor:
    """特徵質量監控器"""

    def __init__(self):
        self.logger = logging.getLogger("hk_quant_system.feature_quality")

    def check_features(self, features: pd.DataFrame) -> Dict[str, Any]:
        """檢查特徵質量"""
        if features.empty:
            return {"overall_quality": 0.0, "issues": ["No features to check"]}

        issues = []
        quality_scores = []

        # 檢查缺失值
        missing_ratio = features.isnull().sum() / len(features)
        high_missing_features = missing_ratio[missing_ratio > 0.1].index.tolist()

        if high_missing_features:
            issues.append(f"High missing values in: {high_missing_features}")
            quality_scores.append(0.7)
        else:
            quality_scores.append(1.0)

        # 檢查異常值
        for col in features.select_dtypes(include=[np.number]).columns:
            Q1 = features[col].quantile(0.25)
            Q3 = features[col].quantile(0.75)
            IQR = Q3 - Q1

            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR

            outliers = features[
                (features[col] < lower_bound) | (features[col] > upper_bound)
            ]
            outlier_ratio = len(outliers) / len(features)

            if outlier_ratio > 0.1:
                issues.append(f"High outliers in {col}: {outlier_ratio:.2%}")
                quality_scores.append(0.8)
            else:
                quality_scores.append(1.0)

        # 檢查數據分布
        for col in features.select_dtypes(include=[np.number]).columns:
            if features[col].std() == 0:
                issues.append(f"Constant feature: {col}")
                quality_scores.append(0.0)
            else:
                quality_scores.append(1.0)

        overall_quality = np.mean(quality_scores)

        return {
            "overall_quality": overall_quality,
            "issues": issues,
            "feature_count": len(features.columns),
            "sample_count": len(features),
            "quality_scores": quality_scores,
        }


# 全局特徵存儲實例
feature_store = AdvancedFeatureStore()
