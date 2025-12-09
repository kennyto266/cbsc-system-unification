"""
CBSC (Callable Bull/Bear Contract) Data Models
牛熊證數據模型定義

This module defines the data models for CBSC products including contract specifications,
sentiment data, and trading signals specifically designed for Hong Kong structured products.

Author: CBSC Backtesting System Team
Date: 2025-12-04
"""

from datetime import datetime, date
from typing import Dict, Any, List, Optional, Union
from decimal import Decimal
from enum import Enum
from pydantic import BaseModel, Field, validator
import pandas as pd
import numpy as np
import logging

class CBSCType(str, Enum):
    """CBSC產品類型"""
    BULL = "BULL"      # 看漲牛熊證
    BEAR = "BEAR"      # 看跌牛熊證

class SentimentLevel(str, Enum):
    """情緒等級"""
    EXTREME_BULL = "EXTREME BULL"
    MOD_BULL = "MOD BULL"
    NEUTRAL = "NEUTRAL"
    MOD_BEAR = "MOD BEAR"
    EXTREME_BEAR = "EXTREME BEAR"

class SignalType(int, Enum):
    """交易信號類型"""
    BUY_BULL = 1      # 買入牛證
    HOLD = 0          # 持有
    SELL_BEAR = -1    # 買入熊證

class CBSCContract(BaseModel):
    """CBSC合約規格"""

    # 基本合約信息
    ticker: str = Field(..., description="牛熊證代碼")
    underlying_ticker: str = Field(..., description="標的資產代碼")
    cbsc_type: CBSCType = Field(..., description="CBSC類型")
    issuer: str = Field(..., description="發行商")

    # 合約規格
    call_price: float = Field(..., gt=0, description="收回價")
    strike_price: float = Field(..., gt=0, description="行使價")
    entitlement_ratio: float = Field(..., gt=0, description="兌換比率")
    leverage_ratio: float = Field(..., gt=1, description="槓桿倍數")

    # 日期信息
    issue_date: date = Field(..., description="發行日期")
    maturity_date: date = Field(..., description="到期日期")
    listing_date: date = Field(..., description="上市日期")

    # 交易信息
    trading_currency: str = Field(default="HKD", description="交易貨幣")
    lot_size: int = Field(default=10000, description="每手交易單位")

    # 風險指標
    call_risk_level: float = Field(default=0.0, ge=0, le=1, description="收回風險等級")
    time_decay_rate: float = Field(default=0.0, ge=0, description="時間衰減率")

    class Config:
        use_enum_values = True

    @validator('maturity_date')
    def validate_maturity_date(cls, v, values):
        """驗證到期日期必須在發行日期之後"""
        if 'issue_date' in values and v <= values['issue_date']:
            raise ValueError('到期日期必須在發行日期之後')
        return v

    @validator('call_price')
    def validate_call_price(cls, v, values):
        """驗證收回價與槓桿倍數的合理性"""
        if 'leverage_ratio' in values and v <= 0:
            raise ValueError('收回價必須大於0')
        return v

    def calculate_distance_to_call(self, current_price: float) -> float:
        """計算當前價格距離收回價的百分比"""
        if current_price <= 0:
            return float('inf')
        return (self.call_price - current_price) / current_price

    def is_near_call(self, current_price: float, buffer: float = 0.05) -> bool:
        """判斷是否接近收回價"""
        distance = self.calculate_distance_to_call(current_price)
        return 0 <= distance <= buffer

    def calculate_time_decay_factor(self, current_date: date) -> float:
        """計算時間衰減因子"""
        if current_date >= self.maturity_date:
            return 0.0

        total_days = (self.maturity_date - self.issue_date).days
        remaining_days = (self.maturity_date - current_date).days

        if remaining_days <= 0:
            return 0.0

        return remaining_days / total_days

class WarrantSentiment(BaseModel):
    """牛熊證市場情緒數據"""

    # 基本信息日期
    date: datetime = Field(..., description="數據日期")
    afternoon_close: float = Field(..., gt=0, description="午後收盤價")
    daily_return: Optional[float] = Field(None, description="日收益率")

    # 牛熊證數據
    bull_ratio: float = Field(..., ge=0, le=1, description="牛證佔比")
    bull_bear_ratio: float = Field(..., gt=0, description="牛熊證成交額比率")
    bull_turnover_hkd: float = Field(..., ge=0, description="牛證成交額(港元)")
    bear_turnover_hkd: float = Field(..., ge=0, description="熊證成交額(港元)")

    # 信號信息
    signal: SignalType = Field(..., description="交易信號")
    sentiment_level: SentimentLevel = Field(..., description="情緒等級")

    # 計算指標
    total_turnover: float = Field(..., ge=0, description="總成交額")
    sentiment_strength: float = Field(..., ge=-1, le=1, description="情緒強度")

    class Config:
        use_enum_values = True

    def __init__(self, **data):
        """初始化時自動計算總成交額和情緒強度"""
        if 'total_turnover' not in data:
            data['total_turnover'] = data.get('bull_turnover_hkd', 0) + data.get('bear_turnover_hkd', 0)

        if 'sentiment_strength' not in data:
            bull_turnover = data.get('bull_turnover_hkd', 0)
            bear_turnover = data.get('bear_turnover_hkd', 0)
            total = bull_turnover + bear_turnover

            if total > 0:
                data['sentiment_strength'] = (bull_turnover - bear_turnover) / total
            else:
                data['sentiment_strength'] = 0.0

        super().__init__(**data)

    def calculate_sentiment_score(self) -> float:
        """計算情緒評分 (0-100, 50為中性)"""
        return (self.sentiment_strength + 1) * 50

    def get_extreme_signal(self) -> bool:
        """判斷是否為極端情緒信號"""
        return self.sentiment_level in [SentimentLevel.EXTREME_BULL, SentimentLevel.EXTREME_BEAR]

class CBSCPortfolioPosition(BaseModel):
    """CBSC投資組合持倉"""

    # 持倉信息
    contract: CBSCContract = Field(..., description="CBSC合約")
    quantity: int = Field(..., description="持倉數量")
    entry_price: float = Field(..., gt=0, description="入場價格")
    entry_date: datetime = Field(..., description="入場日期")

    # 當前狀態
    current_price: Optional[float] = Field(None, description="當前價格")
    current_value: Optional[float] = Field(None, description="當前價值")
    unrealized_pnl: Optional[float] = Field(None, description="未實現損益")

    # 風險指標
    call_risk_exposure: float = Field(default=0.0, ge=0, le=1, description="收回風險敞口")
    leverage_utilization: float = Field(default=0.0, ge=0, le=1, description="槓桿利用率")

    def update_current_state(self, current_price: float) -> None:
        """更新當前狀態"""
        self.current_price = current_price
        self.current_value = self.quantity * current_price
        entry_value = self.quantity * self.entry_price
        self.unrealized_pnl = self.current_value - entry_value

        # 更新風險指標
        self.call_risk_exposure = self.contract.calculate_distance_to_call(current_price)
        self.leverage_utilization = min(1.0, abs(self.unrealized_pnl) / entry_value) if entry_value > 0 else 0.0

    def should_liquidate(self, risk_buffer: float = 0.05) -> bool:
        """判斷是否應該平倉"""
        if self.current_price is None:
            return False

        # 收回價風險檢查
        if self.contract.is_near_call(self.current_price, risk_buffer):
            return True

        # 損失控制檢查 (損失超過20%)
        if self.unrealized_pnl and self.unrealized_pnl < -0.2 * (self.quantity * self.entry_price):
            return True

        return False

class CBSCStrategySignal(BaseModel):
    """CBSC策略信號"""

    # 信號基本信息
    timestamp: datetime = Field(..., description="信號時間戳")
    signal_type: SignalType = Field(..., description="信號類型")
    confidence: float = Field(..., ge=0, le=1, description="信號信心度")

    # 價格信息
    market_price: float = Field(..., gt=0, description="市場價格")
    target_contract: Optional[str] = Field(None, description="目標合約代碼")

    # 情緒信息
    sentiment_data: WarrantSentiment = Field(..., description="情緒數據")
    technical_signal: Optional[float] = Field(None, ge=-1, le=1, description="技術指標信號")

    # 執行信息
    recommended_position_size: float = Field(..., ge=0, description="建議持倉規模")
    risk_level: str = Field(default="MEDIUM", description="風險等級")

    class Config:
        use_enum_values = True

    def generate_signal_id(self) -> str:
        """生成信號ID"""
        return f"{self.timestamp.strftime('%Y%m%d_%H%M%S')}_{self.signal_type.name}_{self.confidence:.2f}"

# 數據處理函數
def parse_warrant_sentiment_csv(csv_path: str) -> List[WarrantSentiment]:
    """解析牛熊證情緒CSV文件"""
    df = pd.read_csv(csv_path)

    sentiment_records = []
    for _, row in df.iterrows():
        try:
            # 處理日期
            date_str = row['Date']
            if isinstance(date_str, str):
                date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            else:
                date_obj = pd.to_datetime(date_str).to_pydatetime()

            # 處理可選字段
            daily_return = None
            if pd.notna(row.get('Daily_Return')) and row.get('Daily_Return') != '':
                daily_return = float(row['Daily_Return'])

            # 創建情緒記錄
            sentiment = WarrantSentiment(
                date=date_obj,
                afternoon_close=float(row['Afternoon_Close']),
                daily_return=daily_return,
                bull_ratio=float(row['Bull_Ratio']),
                bull_bear_ratio=float(row['Bull_Bear_Ratio']),
                bull_turnover_hkd=float(row['Bull_Turnover_HKD']),
                bear_turnover_hkd=float(row['Bear_Turnover_HKD']),
                signal=SignalType(int(row['Signal'])),
                sentiment_level=SentimentLevel(row['Sentiment_Level'])
            )

            sentiment_records.append(sentiment)

        except Exception as e:
            print(f"解析行 {row.name} 時出錯: {e}")
            continue

    return sentiment_records

def create_sample_cbsc_contract() -> CBSCContract:
    """創建示例CBSC合約"""
    from datetime import date

    return CBSCContract(
        ticker="73888.HK",
        underlying_ticker="0700.HK",
        cbsc_type=CBSCType.BULL,
        issuer="UBS",
        call_price=180.0,
        strike_price=280.0,
        entitlement_ratio=0.1,
        leverage_ratio=7.5,
        issue_date=date(2024, 1, 1),
        maturity_date=date(2025, 12, 31),
        listing_date=date(2024, 1, 2),
        call_risk_level=0.3,
        time_decay_rate=0.02
    )

if __name__ == "__main__":
    # 測試代碼
    print("=== CBSC Models 測試 ===")

    # 創建示例合約
    contract = create_sample_cbsc_contract()
    print(f"示例合約: {contract.ticker}")
    print(f"類型: {contract.cbsc_type}")
    print(f"槓桿倍數: {contract.leverage_ratio}")

    # 測試距離收回價計算
    current_price = 260.0
    distance = contract.calculate_distance_to_call(current_price)
    print(f"當前價格 {current_price} 距離收回價: {distance:.2%}")
    print(f"是否接近收回價: {contract.is_near_call(current_price)}")

    # 測試時間衰減
    from datetime import date
    today = date.today()
    decay_factor = contract.calculate_time_decay_factor(today)
    print(f"時間衰減因子: {decay_factor:.2f}")

    print("CBSC Models 測試完成！")


class AdvancedSentimentProcessor:
    """高级情绪分析处理器"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化处理器"""
        self.config = config or {}
        self.strategies = ["direct_rsi", "sentiment_momentum", "composite_index", "volatility_adjusted"]
        self.logger = logging.getLogger("cbsc_models.advanced_sentiment_processor")

    async def process_sentiment_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """处理情绪数据"""
        try:
            # 模拟4种情绪策略处理
            results = {}

            for strategy in self.strategies:
                results[strategy] = {
                    "signal": self._generate_signal(data),
                    "strength": self._calculate_strength(data),
                    "confidence": self._calculate_confidence(data)
                }

            return {
                "timestamp": datetime.now().isoformat(),
                "strategies": results,
                "overall_sentiment": self._calculate_overall_sentiment(results)
            }

        except Exception as e:
            self.logger.error(f"处理情绪数据失败: {e}")
            return {}

    def _generate_signal(self, data: Dict[str, Any]) -> str:
        """生成信号"""
        import random
        signals = ["BUY", "SELL", "HOLD"]
        return random.choice(signals)

    def _calculate_strength(self, data: Dict[str, Any]) -> float:
        """计算信号强度"""
        import random
        return random.uniform(0.3, 1.0)

    def _calculate_confidence(self, data: Dict[str, Any]) -> float:
        """计算置信度"""
        import random
        return random.uniform(0.5, 0.95)

    def _calculate_overall_sentiment(self, results: Dict[str, Any]) -> str:
        """计算整体情绪"""
        buy_signals = sum(1 for r in results.values() if r["signal"] == "BUY")
        sell_signals = sum(1 for r in results.values() if r["signal"] == "SELL")

        if buy_signals > sell_signals:
            return "BULLISH"
        elif sell_signals > buy_signals:
            return "BEARISH"
        else:
            return "NEUTRAL"