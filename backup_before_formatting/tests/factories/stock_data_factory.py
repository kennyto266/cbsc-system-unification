#!/usr/bin/env python3
"""
股票數據工廠
Stock Data Factory for Testing

為測試提供各種類型的股票數據生成工具
"""

import factory
from factory import fuzzy
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import random

@dataclass
class StockMarketData:
    """股票市場數據模型"""
    symbol: str
    timestamp: datetime
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    volume: int

@dataclass
class StockInfo:
    """股票基本信息模型"""
    symbol: str
    name: str
    sector: str
    industry: str
    market_cap: int
    pe_ratio: float
    dividend_yield: float
    currency: str
    exchange: str

class StockMarketDataFactory(factory.Factory):
    """股票市場數據工廠"""

    class Meta:
        model = StockMarketData

    symbol = fuzzy.FuzzyChoice(["0700.HK", "0941.HK", "1398.HK", "0388.HK", "1299.HK"])
    timestamp = fuzzy.FuzzyDateTime(
        datetime.now() - timedelta(days=365),
        datetime.now()
    )

    @factory.lazy_attribute
    def close_price(self):
        return fuzzy.FuzzyFloat(50, 500).fuzz()

    @factory.lazy_attribute
    def open_price(self):
        variation = self.close_price * 0.02  # 2% variation
        return self.close_price + random.uniform(-variation, variation)

    @factory.lazy_attribute
    def high_price(self):
        max_variation = self.close_price * 0.05  # 5% max variation
        return max(self.close_price, self.open_price) + random.uniform(0, max_variation)

    @factory.lazy_attribute
    def low_price(self):
        max_variation = self.close_price * 0.05  # 5% max variation
        return min(self.close_price, self.open_price) - random.uniform(0, max_variation)

    volume = fuzzy.FuzzyInteger(100000, 10000000)

class StockInfoFactory(factory.Factory):
    """股票信息工廠"""

    class Meta:
        model = StockInfo

    symbol = fuzzy.FuzzyChoice(["0700.HK", "0941.HK", "1398.HK", "0388.HK", "1299.HK"])
    name = fuzzy.FuzzyText(length=20)
    sector = fuzzy.FuzzyChoice([
        "Technology", "Finance", "Healthcare", "Energy",
        "Consumer", "Industrial", "Real Estate", "Utilities"
    ])
    industry = fuzzy.FuzzyChoice([
        "Software", "Banking", "Insurance", "Manufacturing",
        "Retail", "Pharmaceuticals", "Telecommunications"
    ])
    market_cap = fuzzy.FuzzyInteger(1000000000, 1000000000000)
    pe_ratio = fuzzy.FuzzyFloat(5, 50)
    dividend_yield = fuzzy.FuzzyFloat(0, 0.1)
    currency = "HKD"
    exchange = "HKEX"

class StockDataGenerator:
    """股票數據生成器 - 提供更複雜的數據生成邏輯"""

    def __init__(self, seed: Optional[int] = None):
        """初始化數據生成器"""
        if seed:
            np.random.seed(seed)
            random.seed(seed)

    def generate_price_series(
        self,
        initial_price: float = 100.0,
        days: int = 252,
        volatility: float = 0.02,
        drift: float = 0.0001,
        trend: Optional[str] = None
    ) -> pd.Series:
        """
        生成價格序列

        Args:
            initial_price: 初始價格
            days: 交易日數
            volatility: 波動率
            drift: 漂移率
            trend: 趨勢方向 ('up', 'down', 'sideways')
        """
        if trend == 'up':
            drift = abs(drift) + 0.001
        elif trend == 'down':
            drift = -abs(drift) - 0.001
        else:  # sideways
            drift = 0.0001

        # 生成隨機漫步價格
        returns = np.random.normal(drift, volatility, days)
        prices = [initial_price]

        for ret in returns[1:]:
            new_price = prices[-1] * (1 + ret)
            # 確保價格為正
            new_price = max(new_price, initial_price * 0.5)
            prices.append(new_price)

        dates = pd.date_range(
            datetime.now() - timedelta(days=days),
            periods=days,
            freq='D'
        )

        return pd.Series(prices, index=dates)

    def generate_ohlcv_data(
        self,
        symbol: str,
        days: int = 252,
        initial_price: float = 100.0,
        trend: Optional[str] = None
    ) -> pd.DataFrame:
        """
        生成完整的OHLCV數據

        Args:
            symbol: 股票代碼
            days: 交易日數
            initial_price: 初始價格
            trend: 趨勢方向
        """
        close_prices = self.generate_price_series(initial_price, days, trend=trend)

        data = []
        for date, close in close_prices.items():
            # 生成開盤價（基於前一日收盤價）
            if len(data) > 0:
                open_variation = close * 0.02
                open_price = max(close + random.uniform(-open_variation, open_variation), close * 0.5)
            else:
                open_price = close

            # 生成最高價和最低價
            high_variation = max(close, open_price) * 0.05
            low_variation = min(close, open_price) * 0.05

            high_price = max(close, open_price) + random.uniform(0, high_variation)
            low_price = min(close, open_price) - random.uniform(0, low_variation)

            # 確保邏輯正確
            high_price = max(high_price, close, open_price)
            low_price = min(low_price, close, open_price)

            # 生成成交量
            base_volume = random.randint(500000, 5000000)
            volume = int(base_volume * random.uniform(0.5, 2.0))

            data.append({
                'symbol': symbol,
                'timestamp': date,
                'open': round(open_price, 2),
                'high': round(high_price, 2),
                'low': round(low_price, 2),
                'close': round(close, 2),
                'volume': volume
            })

        return pd.DataFrame(data)

    def generate_multi_stock_data(
        self,
        symbols: List[str],
        days: int = 252,
        correlation_matrix: Optional[np.ndarray] = None
    ) -> Dict[str, pd.DataFrame]:
        """
        生成多股票相關數據

        Args:
            symbols: 股票代碼列表
            days: 交易日數
            correlation_matrix: 相關性矩陣
        """
        if correlation_matrix is None:
            # 生成默認相關性矩陣
            n_stocks = len(symbols)
            correlation_matrix = np.ones((n_stocks, n_stocks))
            np.fill_diagonal(correlation_matrix, 1.0)

            # 添加一些相關性
            for i in range(n_stocks):
                for j in range(i+1, n_stocks):
                    correlation = random.uniform(0.3, 0.8)
                    correlation_matrix[i, j] = correlation
                    correlation_matrix[j, i] = correlation

        # 生成相關的隨機漫步
        n_stocks = len(symbols)

        # 使用Cholesky分解生成相關的隨機數
        try:
            chol = np.linalg.cholesky(correlation_matrix)
            random_returns = np.random.normal(0, 1, (days, n_stocks))
            correlated_returns = random_returns @ chol.T
        except np.linalg.LinAlgError:
            # 如果相關性矩陣不正定，使用獨立的隨機數
            correlated_returns = np.random.normal(0, 1, (days, n_stocks))

        results = {}
        for i, symbol in enumerate(symbols):
            # 轉換相關回報為價格
            returns = correlated_returns[:, i] * 0.02  # 調整波動率
            prices = [100.0]  # 初始價格

            for ret in returns[1:]:
                new_price = prices[-1] * (1 + ret)
                prices.append(max(new_price, 10.0))  # 最低價格限制

            dates = pd.date_range(
                datetime.now() - timedelta(days=days),
                periods=days,
                freq='D'
            )

            close_series = pd.Series(prices, index=dates)

            # 生成完整的OHLCV數據
            df_data = []
            for date, close in close_series.items():
                if len(df_data) > 0:
                    open_variation = close * 0.02
                    open_price = max(close + random.uniform(-open_variation, open_variation), close * 0.5)
                else:
                    open_price = close

                high_variation = max(close, open_price) * 0.05
                low_variation = min(close, open_price) * 0.05

                high_price = max(close, open_price) + random.uniform(0, high_variation)
                low_price = min(close, open_price) - random.uniform(0, low_variation)

                high_price = max(high_price, close, open_price)
                low_price = min(low_price, close, open_price)

                volume = int(random.randint(500000, 5000000) * random.uniform(0.5, 2.0))

                df_data.append({
                    'symbol': symbol,
                    'timestamp': date,
                    'open': round(open_price, 2),
                    'high': round(high_price, 2),
                    'low': round(low_price, 2),
                    'close': round(close, 2),
                    'volume': volume
                })

            results[symbol] = pd.DataFrame(df_data)

        return results

    def generate_market_regime_data(
        self,
        symbol: str,
        days: int = 504,
        regimes: List[Dict[str, Any]] = None
    ) -> pd.DataFrame:
        """
        生成包含不同市場階段的數據

        Args:
            symbol: 股票代碼
            days: 總交易日數
            regimes: 市場階段配置列表
        """
        if regimes is None:
            regimes = [
                {'start': 0, 'end': 0.2, 'trend': 'up', 'volatility': 0.015, 'name': 'bull_market'},
                {'start': 0.2, 'end': 0.4, 'trend': 'sideways', 'volatility': 0.025, 'name': 'consolidation'},
                {'start': 0.4, 'end': 0.6, 'trend': 'down', 'volatility': 0.03, 'name': 'bear_market'},
                {'start': 0.6, 'end': 0.8, 'trend': 'up', 'volatility': 0.02, 'name': 'recovery'},
                {'start': 0.8, 'end': 1.0, 'trend': 'sideways', 'volatility': 0.015, 'name': 'maturity'}
            ]

        all_data = []
        current_price = 100.0
        total_days = days

        for regime in regimes:
            start_day = int(regime['start'] * total_days)
            end_day = int(regime['end'] * total_days)
            regime_days = end_day - start_day

            if regime_days <= 0:
                continue

            # 生成該階段的數據
            regime_data = self.generate_ohlcv_data(
                symbol,
                regime_days,
                current_price,
                regime['trend']
            )

            # 更新當前價格為該階段的最後價格
            if not regime_data.empty:
                current_price = regime_data['close'].iloc[-1]

            all_data.append(regime_data)

        # 合併所有階段數據
        if all_data:
            return pd.concat(all_data, ignore_index=True)
        else:
            return pd.DataFrame()

    def generate_hibor_data(self, days: int = 365) -> pd.DataFrame:
        """
        生成HIBOR測試數據

        Args:
            days: 天數
        """
        data = []
        base_rate = 3.0  # 基準利率 3%

        for i in range(days):
            date = datetime.now() - timedelta(days=days-i)

            # 生成不同期限的利率
            overnight = base_rate + random.uniform(-0.5, 0.5)
            one_week = overnight + random.uniform(0.1, 0.3)
            one_month = one_week + random.uniform(0.1, 0.3)
            three_month = one_month + random.uniform(0.05, 0.2)
            six_month = three_month + random.uniform(0.05, 0.2)
            twelve_month = six_month + random.uniform(0.05, 0.3)

            # 確保利率邏輯正確
            overnight = max(0.1, overnight)
            rates = [overnight, one_week, one_month, three_month, six_month, twelve_month]
            rates = [max(rates[i], rates[i-1] + 0.05) for i in range(1, len(rates))]

            data.append({
                'date': date.strftime('%Y-%m-%d'),
                'overnight': round(rates[0], 2),
                'one_week': round(rates[1], 2),
                'one_month': round(rates[2], 2),
                'three_month': round(rates[3], 2),
                'six_month': round(rates[4], 2),
                'twelve_month': round(rates[5], 2)
            })

        return pd.DataFrame(data)

# 便捷函數
def create_test_stock_data(symbol: str = "0700.HK", days: int = 100) -> pd.DataFrame:
    """創建測試用股票數據"""
    generator = StockDataGenerator(seed=42)
    return generator.generate_ohlcv_data(symbol, days)

def create_test_hibor_data(days: int = 365) -> pd.DataFrame:
    """創建測試用HIBOR數據"""
    generator = StockDataGenerator(seed=42)
    return generator.generate_hibor_data(days)

def create_bull_market_data(symbol: str = "0700.HK", days: int = 252) -> pd.DataFrame:
    """創建牛市數據"""
    generator = StockDataGenerator(seed=42)
    return generator.generate_ohlcv_data(symbol, days, trend='up')

def create_bear_market_data(symbol: str = "0700.HK", days: int = 252) -> pd.DataFrame:
    """創建熊市數據"""
    generator = StockDataGenerator(seed=42)
    return generator.generate_ohlcv_data(symbol, days, trend='down')

if __name__ == "__main__":
    # 示例用法
    print("生成測試股票數據示例:")
    data = create_test_stock_data("0700.HK", 10)
    print(data.head())

    print("\n生成HIBOR數據示例:")
    hibor = create_test_hibor_data(5)
    print(hibor.head())