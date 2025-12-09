"""
CBSC (Callable Bull/Bear Contract) Data Adapter
牛熊證數據適配器

This module provides data access and processing capabilities for CBSC products including
warrant sentiment data, contract specifications, and market data integration.

Author: CBSC Backtesting System Team
Date: 2025-12-04
"""

import logging
import asyncio
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Union, Tuple
from datetime import datetime, date, timedelta
from pathlib import Path
import json

from .base_adapter import BaseAdapter, DataAdapterConfig, DataSourceType, DataQuality
from ..models.cbsc_models import (
    CBSCContract, WarrantSentiment, CBSCType, SentimentLevel,
    SignalType, parse_warrant_sentiment_csv
)
from ..models.base import BaseConfig

logger = logging.getLogger(__name__)

class CBSCDataAdapterConfig(DataAdapterConfig):
    """CBSC數據適配器配置"""

    # 數據源路徑
    sentiment_data_path: str = Field(..., description="牛熊證情緒數據路徑")
    contract_data_path: Optional[str] = Field(None, description="CBSC合約數據路徑")

    # 數據處理參數
    min_turnover_threshold: float = Field(1000000, gt=0, description="最小成交額閾值")
    sentiment_confidence_threshold: float = Field(0.6, ge=0, le=1, description="情緒信心度閾值")

    # 風險參數
    call_price_buffer: float = Field(0.05, gt=0, le=0.2, description="收回價緩衝區")
    max_leverage_ratio: float = Field(15.0, gt=1, description="最大槓桿倍數")

    # 數據質量
    data_quality_threshold: float = Field(0.8, ge=0, le=1, description="數據質量閾值")

    class Config:
        use_enum_values = True

class CBSCDataAdapter(BaseAdapter):
    """CBSC數據適配器"""

    def __init__(self, config: CBSCDataAdapterConfig):
        super().__init__(config)
        self.config = config
        self._sentiment_cache: Optional[List[WarrantSentiment]] = None
        self._contract_cache: Optional[Dict[str, CBSCContract]] = None

    async def initialize(self) -> bool:
        """初始化適配器"""
        try:
            self.logger.info(f"初始化CBSC數據適配器: {self.config.sentiment_data_path}")

            # 驗證數據文件存在性
            sentiment_path = Path(self.config.sentiment_data_path)
            if not sentiment_path.exists():
                self.logger.error(f"情緒數據文件不存在: {sentiment_path}")
                return False

            # 預加載情緒數據
            await self._load_sentiment_data()

            # 預加載合約數據（如果存在）
            if self.config.contract_data_path:
                await self._load_contract_data()

            self.logger.info("CBSC數據適配器初始化完成")
            return True

        except Exception as e:
            self.logger.error(f"CBSC數據適配器初始化失敗: {e}")
            return False

    async def _load_sentiment_data(self) -> None:
        """加載情緒數據"""
        try:
            self.logger.info("加載牛熊證情緒數據...")
            self._sentiment_cache = parse_warrant_sentiment_csv(self.config.sentiment_data_path)

            # 數據質量檢查
            quality_score = self._assess_sentiment_data_quality(self._sentiment_cache)
            self.logger.info(f"情緒數據質量評分: {quality_score:.2f}")

            if quality_score < self.config.data_quality_threshold:
                self.logger.warning(f"情緒數據質量低於閾值: {quality_score:.2f} < {self.config.data_quality_threshold}")

        except Exception as e:
            self.logger.error(f"加載情緒數據失敗: {e}")
            self._sentiment_cache = []

    async def _load_contract_data(self) -> None:
        """加載CBSC合約數據"""
        try:
            self.logger.info(f"加載CBSC合約數據: {self.config.contract_data_path}")

            contract_path = Path(self.config.contract_data_path)
            if contract_path.exists():
                with open(contract_path, 'r', encoding='utf-8') as f:
                    contract_data = json.load(f)

                self._contract_cache = {}
                for contract_info in contract_data:
                    contract = CBSCContract(**contract_info)
                    self._contract_cache[contract.ticker] = contract

                self.logger.info(f"成功加載 {len(self._contract_cache)} 個CBSC合約")
            else:
                self.logger.warning(f"合約數據文件不存在: {contract_path}")
                self._contract_cache = {}

        except Exception as e:
            self.logger.error(f"加載合約數據失敗: {e}")
            self._contract_cache = {}

    def _assess_sentiment_data_quality(self, sentiment_data: List[WarrantSentiment]) -> float:
        """評估情緒數據質量"""
        if not sentiment_data:
            return 0.0

        quality_factors = []

        # 數據完整性檢查
        total_records = len(sentiment_data)
        valid_records = sum(1 for record in sentiment_data if self._is_valid_sentiment_record(record))
        completeness_score = valid_records / total_records if total_records > 0 else 0.0
        quality_factors.append(completeness_score)

        # 數據一致性檢查
        consistency_score = self._check_data_consistency(sentiment_data)
        quality_factors.append(consistency_score)

        # 極端值檢查
        outlier_score = self._check_outlier_ratio(sentiment_data)
        quality_factors.append(outlier_score)

        return np.mean(quality_factors)

    def _is_valid_sentiment_record(self, record: WarrantSentiment) -> bool:
        """檢查情緒記錄是否有效"""
        if record.total_turnover < self.config.min_turnover_threshold:
            return False

        if record.afternoon_close <= 0:
            return False

        # 檢查情緒強度合理性
        if abs(record.sentiment_strength) > 1.0:
            return False

        return True

    def _check_data_consistency(self, sentiment_data: List[WarrantSentiment]) -> float:
        """檢查數據一致性"""
        if len(sentiment_data) < 2:
            return 1.0

        # 檢查日期順序
        dates = [record.date for record in sentiment_data]
        if dates != sorted(dates):
            return 0.5

        # 檢查價格連續性（沒有異常跳動）
        prices = [record.afternoon_close for record in sentiment_data]
        price_changes = [abs(prices[i+1] - prices[i]) / prices[i] for i in range(len(prices)-1)]

        # 計算異常跳動比例（超過10%的變化）
        extreme_changes = [change for change in price_changes if change > 0.1]
        consistency_score = 1.0 - (len(extreme_changes) / len(price_changes))

        return max(0.0, consistency_score)

    def _check_outlier_ratio(self, sentiment_data: List[WarrantSentiment]) -> float:
        """檢查異常值比例"""
        if not sentiment_data:
            return 1.0

        # 檢查成交額異常值
        turnovers = [record.total_turnover for record in sentiment_data]
        q75, q25 = np.percentile(turnovers, [75, 25])
        iqr = q75 - q25

        if iqr == 0:
            return 1.0

        outliers = [t for t in turnovers if t < q25 - 1.5*iqr or t > q75 + 1.5*iqr]
        outlier_ratio = len(outliers) / len(turnovers)

        return max(0.0, 1.0 - outlier_ratio)

    async def get_sentiment_data(self, start_date: Optional[datetime] = None,
                               end_date: Optional[datetime] = None) -> List[WarrantSentiment]:
        """獲取情緒數據"""
        if not self._sentiment_cache:
            return []

        filtered_data = self._sentiment_cache

        # 按日期篩選
        if start_date:
            filtered_data = [record for record in filtered_data if record.date >= start_date]

        if end_date:
            filtered_data = [record for record in filtered_data if record.date <= end_date]

        return filtered_data

    async def get_latest_sentiment(self) -> Optional[WarrantSentiment]:
        """獲取最新情緒數據"""
        if not self._sentiment_cache:
            return None

        return max(self._sentiment_cache, key=lambda x: x.date)

    async def get_contract_by_ticker(self, ticker: str) -> Optional[CBSCContract]:
        """根據代碼獲取CBSC合約"""
        if not self._contract_cache:
            return None

        return self._contract_cache.get(ticker)

    async def get_contracts_by_underlying(self, underlying_ticker: str) -> List[CBSCContract]:
        """根據標的資產獲取CBSC合約列表"""
        if not self._contract_cache:
            return []

        return [contract for contract in self._contract_cache.values()
                if contract.underlying_ticker == underlying_ticker]

    async def calculate_sentiment_indicators(self, sentiment_data: List[WarrantSentiment]) -> Dict[str, Any]:
        """計算情緒指標"""
        if not sentiment_data:
            return {}

        # 按日期排序
        sorted_data = sorted(sentiment_data, key=lambda x: x.date)

        # 計算移動平均情緒強度
        sentiment_strengths = [record.sentiment_strength for record in sorted_data]
        ma_5 = pd.Series(sentiment_strengths).rolling(5).mean().iloc[-1] if len(sentiment_strengths) >= 5 else np.mean(sentiment_strengths)
        ma_20 = pd.Series(sentiment_strengths).rolling(20).mean().iloc[-1] if len(sentiment_strengths) >= 20 else np.mean(sentiment_strengths)

        # 計算情緒波動率
        volatility = np.std(sentiment_strengths[-20:]) if len(sentiment_strengths) >= 20 else 0.0

        # 計算極端情緒比例
        extreme_count = sum(1 for record in sorted_data[-10:] if record.get_extreme_signal())
        extreme_ratio = extreme_count / min(10, len(sorted_data))

        # 當前情緒狀態
        latest_sentiment = sorted_data[-1]

        return {
            'current_sentiment': latest_sentiment.sentiment_strength,
            'current_level': latest_sentiment.sentiment_level,
            'ma_5_sentiment': ma_5,
            'ma_20_sentiment': ma_20,
            'sentiment_volatility': volatility,
            'extreme_sentiment_ratio': extreme_ratio,
            'data_points': len(sentiment_data),
            'quality_score': self._assess_sentiment_data_quality(sentiment_data)
        }

    async def filter_by_signal_strength(self, sentiment_data: List[WarrantSentiment],
                                      min_confidence: Optional[float] = None) -> List[WarrantSentiment]:
        """根據信號強度篩選情緒數據"""
        if not sentiment_data:
            return []

        threshold = min_confidence or self.config.sentiment_confidence_threshold

        # 篩選高信心度記錄
        filtered_data = []
        for record in sentiment_data:
            # 極端情緒且高成交額
            if record.get_extreme_signal() and record.total_turnover >= self.config.min_turnover_threshold:
                filtered_data.append(record)
            # 非極端情緒但信心度高
            elif abs(record.sentiment_strength) >= threshold:
                filtered_data.append(record)

        return filtered_data

    async def get_data_summary(self) -> Dict[str, Any]:
        """獲取數據摘要"""
        sentiment_count = len(self._sentiment_cache) if self._sentiment_cache else 0
        contract_count = len(self._contract_cache) if self._contract_cache else 0

        latest_sentiment = await self.get_latest_sentiment()

        summary = {
            'sentiment_records': sentiment_count,
            'contracts_available': contract_count,
            'data_quality_score': self._assess_sentiment_data_quality(self._sentiment_cache) if self._sentiment_cache else 0.0,
            'latest_sentiment_date': latest_sentiment.date if latest_sentiment else None,
            'latest_sentiment_level': latest_sentiment.sentiment_level if latest_sentiment else None,
            'configuration': {
                'sentiment_data_path': self.config.sentiment_data_path,
                'min_turnover_threshold': self.config.min_turnover_threshold,
                'sentiment_confidence_threshold': self.config.sentiment_confidence_threshold,
                'call_price_buffer': self.config.call_price_buffer
            }
        }

        return summary

    async def refresh_data(self) -> bool:
        """刷新數據"""
        try:
            self.logger.info("刷新CBSC數據...")

            # 清除緩存
            self._sentiment_cache = None
            self._contract_cache = None

            # 重新加載數據
            await self._load_sentiment_data()
            await self._load_contract_data()

            self.logger.info("CBSC數據刷新完成")
            return True

        except Exception as e:
            self.logger.error(f"刷新CBSC數據失敗: {e}")
            return False

    async def cleanup(self) -> None:
        """清理資源"""
        self.logger.info("清理CBSC數據適配器資源...")
        self._sentiment_cache = None
        self._contract_cache = None

# 工廠函數
async def create_cbsc_adapter(sentiment_data_path: str,
                            contract_data_path: Optional[str] = None,
                            **kwargs) -> CBSCDataAdapter:
    """創建CBSC數據適配器"""

    config = CBSCDataAdapterConfig(
        source_type=DataSourceType.CUSTOM,
        source_path=sentiment_data_path,
        sentiment_data_path=sentiment_data_path,
        contract_data_path=contract_data_path,
        **kwargs
    )

    adapter = CBSCDataAdapter(config)
    success = await adapter.initialize()

    if not success:
        raise RuntimeError("CBSC數據適配器初始化失敗")

    return adapter

if __name__ == "__main__":
    # 測試代碼
    async def test_cbsc_adapter():
        print("=== CBSC Data Adapter 測試 ===")

        # 創建適配器
        adapter_config = CBSCDataAdapterConfig(
            source_type=DataSourceType.CUSTOM,
            source_path="./CODEX--/warrant_sentiment_daily.csv",
            sentiment_data_path="./CODEX--/warrant_sentiment_daily.csv"
        )

        adapter = CBSCDataAdapter(adapter_config)

        # 初始化
        success = await adapter.initialize()
        print(f"適配器初始化: {'成功' if success else '失敗'}")

        if success:
            # 獲取數據摘要
            summary = await adapter.get_data_summary()
            print(f"數據摘要: {summary}")

            # 獲取最新情緒
            latest_sentiment = await adapter.get_latest_sentiment()
            if latest_sentiment:
                print(f"最新情緒: {latest_sentiment.sentiment_level} ({latest_sentiment.sentiment_strength:.3f})")

            # 計算情緒指標
            sentiment_data = await adapter.get_sentiment_data()
            if sentiment_data:
                indicators = await adapter.calculate_sentiment_indicators(sentiment_data)
                print(f"情緒指標: {indicators}")

        # 清理
        await adapter.cleanup()
        print("CBSC Data Adapter 測試完成！")

    # 運行測試
    asyncio.run(test_cbsc_adapter())