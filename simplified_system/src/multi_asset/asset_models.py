#!/usr/bin/env python3
"""
香港專用資產數據模型 - Hong Kong Exclusive Asset Data Models
專注於香港股票市場的數據結構，包括港股、REIT、權證、ETF等
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List, Union
from enum import Enum
import pandas as pd
import numpy as np
from decimal import Decimal

class AssetClass(Enum):
    """香港資產類別枚举"""
    EQUITY = "equity"           # 香港股票
    REIT = "reit"               # 房地产投资信托基金
    WARRANT = "warrant"         # 衍生权证
    ETF = "etf"                 # 交易所交易基金
    TRUST = "trust"             # 信托产品

class MarketRegion(Enum):
    """香港市場區域枚举"""
    HONG_KONG = "hong_kong"
    ASIA = "asia"

class Timeframe(Enum):
    """时间周期枚举"""
    TICK_1S = "1s"              # 1秒
    TICK_1M = "1m"              # 1分钟
    TICK_5M = "5m"              # 5分钟
    TICK_15M = "15m"            # 15分钟
    TICK_30M = "30m"            # 30分钟
    TICK_1H = "1h"              # 1小时
    TICK_4H = "4h"              # 4小时
    TICK_1D = "1d"              # 1天
    TICK_1W = "1w"              # 1周

class Exchange(Enum):
    """香港交易所枚举"""
    HKEX = "HKEX"               # 香港交易所

@dataclass
class MarketData:
    """香港市場數據模型"""
    # 基础标识
    symbol: str                 # 香港標準化符号 (如: 0700.HK, 0941.HK, 1398.HK)
    asset_class: AssetClass     # 资产类别
    exchange: Exchange          # 交易所
    region: MarketRegion        # 市场区域

    # 时间信息
    timestamp: datetime         # 时间戳 (UTC)
    timeframe: Timeframe        # 时间周期

    # OHLCV数据 (通用)
    open: float                 # 开盘价
    high: float                 # 最高价
    low: float                  # 最低价
    close: float                # 收盘价
    volume: float               # 成交量

    # 市场深度数据 (外汇/加密货币)
    bid: Optional[float] = None         # 买价
    ask: Optional[float] = None         # 卖价
    bid_size: Optional[float] = None    # 买量
    ask_size: Optional[float] = None    # 卖量
    spread: Optional[float] = None      # 买卖价差

    # 衍生品数据
    open_interest: Optional[float] = None    # 未平仓合约
    funding_rate: Optional[float] = None     # 资金费率
    mark_price: Optional[float] = None       # 标记价格
    index_price: Optional[float] = None      # 指数价格

    # 财务指标
    market_cap: Optional[float] = None      # 市值
    circulating_supply: Optional[float] = None  # 流通供应量

    # 元数据
    currency: str = "USD"       # 报价货币
    session: Optional[str] = None      # 交易时段
    is_active: bool = True       # 是否活跃交易

    def to_dataframe(self) -> pd.DataFrame:
        """转换为单行DataFrame"""
        data = {
            'timestamp': [self.timestamp],
            'symbol': [self.symbol],
            'open': [self.open],
            'high': [self.high],
            'low': [self.low],
            'close': [self.close],
            'volume': [self.volume],
            'asset_class': [self.asset_class.value],
            'exchange': [self.exchange.value]
        }

        # 添加可选字段
        optional_fields = ['bid', 'ask', 'spread', 'market_cap', 'open_interest']
        for field in optional_fields:
            value = getattr(self, field)
            if value is not None:
                data[field] = [value]

        return pd.DataFrame(data)

    @classmethod
    def from_dataframe(cls, df: pd.DataFrame, index: int = 0) -> 'MarketData':
        """从DataFrame创建MarketData对象"""
        row = df.iloc[index]

        return cls(
            symbol=row['symbol'],
            asset_class=AssetClass(row['asset_class']),
            exchange=Exchange(row['exchange']),
            region=MarketRegion.GLOBAL,  # 默认全球
            timestamp=pd.to_datetime(row['timestamp']),
            timeframe=Timeframe.TICK_1H,  # 默认1小时
            open=float(row['open']),
            high=float(row['high']),
            low=float(row['low']),
            close=float(row['close']),
            volume=float(row['volume']),
            bid=float(row.get('bid', 0)) if 'bid' in row and pd.notna(row['bid']) else None,
            ask=float(row.get('ask', 0)) if 'ask' in row and pd.notna(row['ask']) else None,
            spread=float(row.get('spread', 0)) if 'spread' in row and pd.notna(row['spread']) else None,
            market_cap=float(row.get('market_cap', 0)) if 'market_cap' in row and pd.notna(row['market_cap']) else None,
            open_interest=float(row.get('open_interest', 0)) if 'open_interest' in row and pd.notna(row['open_interest']) else None
        )

@dataclass
class TickerInfo:
    """资产基本信息"""
    symbol: str
    name: str
    asset_class: AssetClass
    exchange: Exchange
    description: str = ""
    sector: str = ""
    industry: str = ""
    market_cap: Optional[float] = None
    currency: str = "USD"
    min_order_size: float = 0.001
    max_order_size: float = 1000000
    tick_size: float = 0.01
    lot_size: float = 1
    trading_hours: Dict[str, str] = field(default_factory=dict)
    margin_requirements: Dict[str, float] = field(default_factory=dict)

@dataclass
class MultiAssetPortfolio:
    """多资产组合"""
    name: str
    positions: Dict[str, float] = field(default_factory=dict)  # symbol -> quantity
    cash: float = 1000000  # 初始现金
    currency: str = "USD"
    created_at: datetime = field(default_factory=datetime.utcnow)

    def get_total_value(self, prices: Dict[str, float]) -> float:
        """计算组合总价值"""
        total_value = self.cash
        for symbol, quantity in self.positions.items():
            if symbol in prices:
                total_value += quantity * prices[symbol]
        return total_value

    def get_weights(self, prices: Dict[str, float]) -> Dict[str, float]:
        """计算资产权重"""
        total_value = self.get_total_value(prices)
        weights = {'cash': self.cash / total_value}

        for symbol, quantity in self.positions.items():
            if symbol in prices and total_value > 0:
                weights[symbol] = (quantity * prices[symbol]) / total_value

        return weights

# 香港市場預定義資產符號映射
ASSET_SYMBOLS = {
    # 恒生指數成分股 - 主要藍籌股
    "0700.HK": {"symbol": "0700.HK", "asset_class": AssetClass.EQUITY, "exchange": Exchange.HKEX, "name": "騰訊控股"},
    "0941.HK": {"symbol": "0941.HK", "asset_class": AssetClass.EQUITY, "exchange": Exchange.HKEX, "name": "中國移動"},
    "1299.HK": {"symbol": "1299.HK", "asset_class": AssetClass.EQUITY, "exchange": Exchange.HKEX, "name": "友邦保險"},
    "2318.HK": {"symbol": "2318.HK", "asset_class": AssetClass.EQUITY, "exchange": Exchange.HKEX, "name": "中國平安"},
    "0388.HK": {"symbol": "0388.HK", "asset_class": AssetClass.EQUITY, "exchange": Exchange.HKEX, "name": "港交所"},
    "1398.HK": {"symbol": "1398.HK", "asset_class": AssetClass.EQUITY, "exchange": Exchange.HKEX, "name": "工商銀行"},
    "0005.HK": {"symbol": "0005.HK", "asset_class": AssetClass.EQUITY, "exchange": Exchange.HKEX, "name": "匯豐控股"},
    "0002.HK": {"symbol": "0002.HK", "asset_class": AssetClass.EQUITY, "exchange": Exchange.HKEX, "name": "中電控股"},
    "0011.HK": {"symbol": "0011.HK", "asset_class": AssetClass.EQUITY, "exchange": Exchange.HKEX, "name": "恆生銀行"},
    "0013.HK": {"symbol": "0013.HK", "asset_class": AssetClass.EQUITY, "exchange": Exchange.HKEX, "name": "和記黃埔"},

    # 主要香港ETF
    "02800.HK": {"symbol": "02800.HK", "asset_class": AssetClass.ETF, "exchange": Exchange.HKEX, "name": "恒生中國企業指數ETF"},
    "02833.HK": {"symbol": "02833.HK", "asset_class": AssetClass.ETF, "exchange": Exchange.HKEX, "name": "恒生指數ETF"},
    "03033.HK": {"symbol": "03033.HK", "asset_class": AssetClass.ETF, "exchange": Exchange.HKEX, "name": "恒生科技指數ETF"},

    # 主要香港REIT
    "00775.HK": {"symbol": "00775.HK", "asset_class": AssetClass.REIT, "exchange": Exchange.HKEX, "name": "領展房產基金"},
    "04086.HK": {"symbol": "04086.HK", "asset_class": AssetClass.REIT, "exchange": Exchange.HKEX, "name": "置富產業信託"},
}

def parse_symbol(symbol: str) -> Dict[str, Any]:
    """解析香港市場符號，返回資產信息"""
    # 預定義符號直接返回
    if symbol in ASSET_SYMBOLS:
        return ASSET_SYMBOLS[symbol]

    # 港股識別 (0700.HK 或 0700 格式)
    if symbol.endswith('.HK'):
        return {
            "symbol": symbol,
            "asset_class": AssetClass.EQUITY,
            "exchange": Exchange.HKEX,
            "region": MarketRegion.HONG_KONG
        }
    elif len(symbol) == 4 and symbol.isdigit():
        # 4位數字代碼，轉換為港股格式
        hk_symbol = f"0{symbol}.HK"
        return {
            "symbol": hk_symbol,
            "asset_class": AssetClass.EQUITY,
            "exchange": Exchange.HKEX,
            "region": MarketRegion.HONG_KONG
        }
    elif len(symbol) == 5 and symbol.isdigit():
        # 5位數字代碼，轉換為港股格式
        hk_symbol = f"{symbol}.HK"
        return {
            "symbol": hk_symbol,
            "asset_class": AssetClass.EQUITY,
            "exchange": Exchange.HKEX,
            "region": MarketRegion.HONG_KONG
        }

    # ETF識別 (通常為5位數字，如02833)
    elif len(symbol) == 5 and symbol.startswith('0') and symbol[1] != '0':
        etf_symbol = f"{symbol}.HK"
        return {
            "symbol": etf_symbol,
            "asset_class": AssetClass.ETF,
            "exchange": Exchange.HKEX,
            "region": MarketRegion.HONG_KONG
        }

    # REIT識別 (通常為5位數字)
    elif len(symbol) == 5 and symbol.startswith('0'):
        reit_symbol = f"{symbol}.HK"
        return {
            "symbol": reit_symbol,
            "asset_class": AssetClass.REIT,
            "exchange": Exchange.HKEX,
            "region": MarketRegion.HONG_KONG
        }

    # 默認認為是港股
    else:
        hk_symbol = symbol if symbol.endswith('.HK') else f"{symbol}.HK"
        return {
            "symbol": hk_symbol,
            "asset_class": AssetClass.EQUITY,
            "exchange": Exchange.HKEX,
            "region": MarketRegion.HONG_KONG
        }

def get_trading_hours(asset_class: AssetClass, region: MarketRegion = MarketRegion.HONG_KONG) -> Dict[str, str]:
    """獲取香港市場交易時間"""
    hk_trading_hours = {
        AssetClass.EQUITY: {
            "open": "09:30",
            "close": "16:00",
            "lunch_start": "12:00",
            "lunch_end": "13:00",
            "timezone": "HKT",
            "market": "香港交易所"
        },
        AssetClass.ETF: {
            "open": "09:30",
            "close": "16:00",
            "lunch_start": "12:00",
            "lunch_end": "13:00",
            "timezone": "HKT",
            "market": "香港交易所"
        },
        AssetClass.REIT: {
            "open": "09:30",
            "close": "16:00",
            "lunch_start": "12:00",
            "lunch_end": "13:00",
            "timezone": "HKT",
            "market": "香港交易所"
        },
        AssetClass.WARRANT: {
            "open": "09:30",
            "close": "16:00",
            "lunch_start": "12:00",
            "lunch_end": "13:00",
            "timezone": "HKT",
            "market": "香港交易所"
        },
        AssetClass.TRUST: {
            "open": "09:30",
            "close": "16:00",
            "lunch_start": "12:00",
            "lunch_end": "13:00",
            "timezone": "HKT",
            "market": "香港交易所"
        }
    }

    return hk_trading_hours.get(asset_class, {
        "open": "09:30",
        "close": "16:00",
        "lunch_start": "12:00",
        "lunch_end": "13:00",
        "timezone": "HKT",
        "market": "香港交易所"
    })

def is_hk_market_open() -> bool:
    """檢查香港市場是否開盤"""
    from datetime import datetime, timezone
    import pytz

    hk_tz = pytz.timezone('Asia/Hong_Kong')
    hk_time = datetime.now(hk_tz)

    # 檢查是否為週末
    if hk_time.weekday() >= 5:  # 週六、週日
        return False

    # 檢查是否在交易時間內
    current_time = hk_time.time()
    morning_start = hk_time.replace(hour=9, minute=30).time()
    morning_end = hk_time.replace(hour=12, minute=0).time()
    afternoon_start = hk_time.replace(hour=13, minute=0).time()
    afternoon_end = hk_time.replace(hour=16, minute=0).time()

    return (morning_start <= current_time <= morning_end or
            afternoon_start <= current_time <= afternoon_end)