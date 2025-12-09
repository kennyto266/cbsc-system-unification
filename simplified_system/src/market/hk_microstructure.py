#!/usr/bin/env python3
"""
香港市場微結構建模 - Hong Kong Market Microstructure Modeling
實現香港特有的市場機制和交易行為分析
Hong Kong Market Microstructure Modeling - Implementing HK-specific market mechanisms and trading behavior analysis
"""

import numpy as np
import pandas as pd
from datetime import datetime, time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import asyncio
import logging

logger = logging.getLogger(__name__)

class HKTradingPhase(Enum):
    """香港交易時段"""
    PRE_OPENING = "pre_opening"      # 09:00-09:30 開市前競價
    MORNING_AUCTION = "morning_auction"  # 09:30 隨機競價
    CONTINUOUS_MORNING = "continuous_morning"  # 09:30-12:00 連續交易
    LUNCH_BREAK = "lunch_break"        # 12:00-13:00 午休
    AFTERNOON_RESUMPTION = "afternoon_resumption"  # 13:00 收盤前競價
    CONTINUOUS_AFTERNOON = "continuous_afternoon"  # 13:00-16:00 連續交易
    CLOSING_AUCTION = "closing_auction"    # 16:00 隨機收盤
    CLOSED = "closed"                    # 收盤後

class HKOrderType(Enum):
    """香港訂單類型"""
    MARKET = "market"          # 市價單
    LIMIT = "limit"            # 限價單
    ENHANCED_LIMIT = "enhanced_limit"  # 增強限價單
    AT_AUCTION_LIMIT = "at_auction_limit"  # 競價限價單
    AT_AUCTION_MARKET = "at_auction_market"  # 競價市價單

class HKMarketMaker:
    """香港市場莊家模擬"""

    def __init__(self, symbol: str, inventory: float = 1000000):
        self.symbol = symbol
        self.inventory = inventory
        self.bid_ask_spread = 0.001  # 0.1% 點差
        self.min_tick_size = self._get_min_tick_size(symbol)
        self.max_order_size = 1000000

    def _get_min_tick_size(self, symbol: str) -> float:
        """獲取最小價格單位"""
        # 根據香港交易所規則
        try:
            price = float(symbol.replace('.HK', ''))
            if price >= 5000:
                return 0.05
            elif price >= 1000:
                return 0.02
            elif price >= 100:
                return 0.01
            elif price >= 50:
                return 0.005
            else:
                return 0.001
        except:
            return 0.01

@dataclass
class HKOrder:
    """香港訂單"""
    symbol: str
    side: str  # 'buy' or 'sell'
    order_type: HKOrderType
    price: Optional[float]
    quantity: int
    timestamp: datetime
    trader_id: str
    phase: HKTradingPhase
    time_in_force: str = "day"  # IOC, FOK, DAY

@dataclass
class HKTrade:
    """香港交易記錄"""
    symbol: str
    price: float
    quantity: int
    timestamp: datetime
    trade_id: str
    buyer_order_id: str
    seller_order_id: str
    phase: HKTradingPhase
    venue: str  # SEHK, AMS, etc

class HKOrderBook:
    """香港訂單簿"""

    def __init__(self, symbol: str, depth_levels: int = 5):
        self.symbol = symbol
        self.depth_levels = depth_levels
        self.bids = []  # 買單 [price, quantity]
        self.asks = []  # 賣單 [price, quantity]
        self.best_bid = 0
        self.best_ask = float('inf')
        self.spread = float('inf')
        self.last_update = datetime.now()

    def update(self, bids: List[Tuple[float, int]], asks: List[Tuple[float, int]]):
        """更新訂單簿"""
        self.bids = sorted(bids, reverse=True)[:self.depth_levels]
        self.asks = sorted(asks)[:self.depth_levels]

        if self.bids:
            self.best_bid = self.bids[0][0]
        if self.asks:
            self.best_ask = self.asks[0][0]

        self.spread = self.best_ask - self.best_bid if self.bids and self.asks else float('inf')
        self.last_update = datetime.now()

class HKMarketMicrostructureAnalyzer:
    """香港市場微結構分析器"""

    def __init__(self, symbol: str):
        self.symbol = symbol
        self.trades: List[HKTrade] = []
        self.orders: List[HKOrder] = []
        self.order_book = HKOrderBook(symbol)
        self.market_makers: Dict[str, HKMarketMaker] = {}
        self.liquidity_measures = {}

    def add_trade(self, trade: HKTrade):
        """添加交易記錄"""
        self.trades.append(trade)

    def add_order(self, order: HKOrder):
        """添加訂單"""
        self.orders.append(order)

    def calculate_liquidity_measures(self) -> Dict[str, float]:
        """計算流動性指標"""
        if len(self.trades) < 10:
            return {}

        trades_df = pd.DataFrame([{
            'price': t.price,
            'quantity': t.quantity,
            'timestamp': t.timestamp
        } for t in self.trades])

        # 1. Amihud Illiquidity Ratio
        returns = trades_df['price'].pct_change().dropna()
        volumes = trades_df['quantity']
        illiquidity = (np.abs(returns) * volumes).mean()

        # 2. Roll's Effective Spread
        price_changes = trades_df['price'].diff().dropna()
        squared_changes = price_changes ** 2
        effective_spread = np.sqrt(squared_changes.mean())

        # 3. Kyle's Lambda (Price Impact)
        volume_sums = volumes.cumsum()
        price_moves = trades_df['price'] - trades_df['price'].iloc[0]
        lambda_kyle = (price_moves / volume_sums).mean()

        # 4. Liquidity-Taking vs Providing
        aggressive_ratio = len(self.orders) / len(self.trades) if self.trades else 0

        self.liquidity_measures = {
            'amihud_illiquidity': illiquidity,
            'effective_spread': effective_spread,
            'kyle_lambda': lambda_kyle,
            'aggressive_ratio': aggressive_ratio,
            'trading_volume_24h': trades_df['quantity'].sum(),
            'trading_value_24h': (trades_df['price'] * trades_df['quantity']).sum(),
            'avg_trade_size': trades_df['quantity'].mean(),
            'volatility': returns.std(),
            'spread_percentage': self.order_book.spread / self.order_book.best_bid if self.order_book.best_bid > 0 else 0
        }

        return self.liquidity_measures

    def analyze_auction_dynamics(self) -> Dict[str, Any]:
        """分析競價機制"""
        auction_trades = [t for t in self.trades if t.phase in [HKTradingPhase.MORNING_AUCTION, HKTradingPhase.CLOSING_AUCTION]]

        if not auction_trades:
            return {}

        # 競價集中度
        prices = [t.price for t in auction_trades]
        price_std = np.std(prices)
        price_range = max(prices) - min(prices)

        # 競價不平衡度
        total_volume = sum(t.quantity for t in auction_trades)
        imbalance = abs(total_volume % 2 - total_volume) / total_volume

        return {
            'auction_volume': total_volume,
            'auction_trades': len(auction_trades),
            'price_discovery_range': price_range,
            'price_discovery_std': price_std,
            'order_imbalance': imbalance,
            'auction_efficiency': price_std / price_range if price_range > 0 else 0
        }

    def detect_market_makers(self) -> Dict[str, Dict[str, Any]]:
        """檢測市場莊家行為"""
        if len(self.orders) < 100:
            return {}

        orders_df = pd.DataFrame([{
            'price': o.price,
            'quantity': o.quantity,
            'timestamp': o.timestamp,
            'trader_id': o.trader_id
        } for o in self.orders if o.price is not None])

        # 按交易者分組
        trader_stats = {}
        for trader_id, group in orders_df.groupby('trader_id'):
            trader_stats[trader_id] = {
                'order_count': len(group),
                'avg_order_size': group['quantity'].mean(),
                'price_consistency': 1 - (group['price'].std() / group['price'].mean()),
                'submission_pattern': self._analyze_submission_pattern(group),
                'total_volume': group['quantity'].sum(),
                'is_liquidity_provider': self._is_liquidity_provider(group)
            }

        return trader_stats

    def _analyze_submission_pattern(self, trader_orders: pd.DataFrame) -> str:
        """分析提交模式"""
        time_diffs = trader_orders['timestamp'].diff().dt.total_seconds()
        avg_interval = time_diffs.mean()

        if avg_interval < 1:
            return "high_frequency"
        elif avg_interval < 10:
            return "normal"
        elif avg_interval < 60:
            return "periodic"
        else:
            return "sporadic"

    def _is_liquidity_provider(self, trader_orders: pd.DataFrame) -> bool:
        """判斷是否為流動性提供者"""
        if len(trader_orders) < 20:
            return False

        # 檢查是否同時掛買賣單
        buy_orders = trader_orders[trader_orders.apply(lambda x: 'buy' in str(x), axis=1)]
        sell_orders = trader_orders[trader_orders.apply(lambda x: 'sell' in str(x), axis=1)]

        return len(buy_orders) > 0 and len(sell_orders) > 0

class HKTradingSessionAnalyzer:
    """香港交易時段分析器"""

    def __init__(self):
        self.session_phases = []
        self.volume_by_phase = {}
        self.price_impact_by_phase = {}

    def analyze_session_patterns(self, trades: List[HKTrade]) -> Dict[str, Any]:
        """分析交易時段模式"""
        if not trades:
            return {}

        # 按時段分組
        phase_stats = {}
        for trade in trades:
            phase = trade.phase.value
            if phase not in phase_stats:
                phase_stats[phase] = []
            phase_stats[phase].append(trade)

        results = {}
        for phase, phase_trades in phase_stats.items():
            if not phase_trades:
                continue

            prices = [t.price for t in phase_trades]
            volumes = [t.quantity for t in phase_trades]

            results[phase] = {
                'trade_count': len(phase_trades),
                'total_volume': sum(volumes),
                'total_value': sum(p * v for p, v in zip(prices, volumes)),
                'price_change': prices[-1] - prices[0] if len(prices) > 1 else 0,
                'price_volatility': pd.Series(prices).std(),
                'avg_trade_size': np.mean(volumes),
                'volume_share': 0  # 稍後計算
            }

        # 計算交易量份額
        total_volume = sum(stats['total_volume'] for stats in results.values())
        for phase in results:
            results[phase]['volume_share'] = results[phase]['total_volume'] / total_volume if total_volume > 0 else 0

        return results

class HKRiskManager:
    """香港市場風險管理"""

    def __init__(self):
        self.risk_limits = {
            'max_position_size': 0.05,  # 5% 單個倉位
            'max_daily_loss': 0.02,  # 2% 日內最大虧損
            'max_total_exposure': 1.0,  # 100% 總倉位
            'min_margin_requirement': 0.15,  # 15% 保證金
        }

        self.emergency_situations = {
            'extreme_volatility': 0.05,  # 5% 極端波動率
            'liquidity_crisis': 0.1,  # 流動性危機
            'system_overload': 0.95,  # 系統過載
        }

    def check_risk_metrics(self, portfolio_value: float, positions: Dict[str, float],
                          current_prices: Dict[str, float]) -> Dict[str, Any]:
        """檢查風險指標"""
        risks = {}

        # 計算倉位價值
        position_values = {}
        total_exposure = 0

        for symbol, quantity in positions.items():
            if symbol in current_prices:
                value = quantity * current_prices[symbol]
                position_values[symbol] = value
                total_exposure += abs(value)

        # 檢查倉位大小限制
        max_position_size = max(position_values.values(), 0)
        position_limit_risk = max_position_size / portfolio_value
        risks['position_size_risk'] = {
            'current': position_limit_risk,
            'limit': self.risk_limits['max_position_size'],
            'breach': position_limit_risk > self.risk_limits['max_position_size'],
            'largest_position': max(position_values.items(), key=lambda x: abs(x[1]))
        }

        # 檢查總倉位暴露
        total_exposure_risk = total_exposure / portfolio_value
        risks['exposure_risk'] = {
            'current': total_exposure_risk,
            'limit': self.risk_limits['max_total_exposure'],
            'breach': total_exposure_risk > self.risk_limits['max_total_exposure']
        }

        # 計算投資組合風險
        portfolio_value_change = self._calculate_portfolio_var(position_values, current_prices)
        risks['portfolio_risk'] = {
            'var_95': portfolio_value_change,
            'max_loss_limit': self.risk_limits['max_daily_loss'],
            'breach': abs(portfolio_value_change) > self.risk_limits['max_daily_loss']
        }

        return risks

    def _calculate_portfolio_var(self, position_values: Dict[str, float],
                                current_prices: Dict[str, float]) -> float:
        """計算投資組合VaR"""
        if not position_values:
            return 0

        # 簡化VaR計算（基於歷史模擬）
        returns = []
        for i in range(1000):  # 蒙特卡羅模擬
            shocked_prices = {}
            for symbol in position_values:
                if symbol in current_prices:
                    # 假設2%日波動率
                    shock = np.random.normal(0, 0.02)
                    shocked_prices[symbol] = current_prices[symbol] * (1 + shock)

            shocked_value = sum(pos * shocked_prices.get(sym, price)
                               for sym, pos in position_values.items()
                               for sym, price in current_prices.items())

            returns.append((shocked_value - sum(position_values.values())) / sum(position_values.values()))

        # 95%分位數
        return np.percentile(returns, 5)

    def monitor_emergency_situations(self, market_metrics: Dict[str, float]) -> Dict[str, bool]:
        """監控緊急情況"""
        emergency_alerts = {}

        for situation, threshold in self.emergency_situations.items():
            metric_value = market_metrics.get(situation.replace('_', ''), 0)
            emergency_alerts[situation] = abs(metric_value) > threshold

        return emergency_alerts

class HKMarketSentimentAnalyzer:
    """香港市場情緒分析器"""

    def __init__(self):
        self.sentiment_indicators = {
            'vix_equivalent': None,      # 香港VIX等價
            'put_call_ratio': None,       # 賣權比
            'margin_trading_level': None, # 保證金交易水平
            'short_interest': None,        # 融券餘額
            'institutional_flow': None   # 機構性資金流
        }

    def analyze_market_sentiment(self, hibor_rate: float,
                                  southbound_flow: float) -> Dict[str, Any]:
        """分析市場情緒"""
        sentiment = {
            'market_risk_appetite': self._assess_risk_appetite(hibor_rate),
            'mainland_confidence': self._assess_mainland_confidence(southbound_flow),
            'liquidity_pressure': self._assess_liquidity_pressure(hibor_rate),
            'overall_sentiment': 'neutral'
        }

        # 綜合評分
        risk_score = sentiment['market_risk_appetite']
        confidence_score = sentiment['mainland_confidence']

        if risk_score > 0.7 and confidence_score > 0.7:
            sentiment['overall_sentiment'] = 'bullish'
        elif risk_score < 0.3 or confidence_score < 0.3:
            sentiment['overall_sentiment'] = 'bearish'
        else:
            sentiment['overall_sentiment'] = 'neutral'

        return sentiment

    def _assess_risk_appetite(self, hibor_rate: float) -> float:
        """評估風險偏好"""
        # HIBOR越低，風險偏好越高
        max_rate = 0.08  # 8%
        min_rate = 0.001  # 0.1%

        normalized_rate = (hibor_rate - min_rate) / (max_rate - min_rate)
        return max(0, min(1, 1 - normalized_rate))

    def _assess_mainland_confidence(self, southbound_flow: float) -> float:
        """評估內地投資者信心"""
        # 南向資金流越大，信心越高
        max_flow = 100  # 假設最大值
        normalized_flow = min(1, max(0, southbound_flow / max_flow))
        return normalized_flow

    def _assess_liquidity_pressure(self, hibor_rate: float) -> float:
        """評估流動性壓力"""
        # HIBOR走高表示流動性緊張
        max_rate = 0.08
        normalized_rate = hibor_rate / max_rate
        return normalized_rate

# 使用示例
def main():
    """主函數 - 展示香港市場微結構分析"""
    analyzer = HKMarketMicrostructureAnalyzer("0700.HK")

    # 模擬一些交易數據
    current_time = datetime.now()

    # 添加模擬交易
    for i in range(100):
        price = 300 + np.random.normal(0, 2)
        quantity = np.random.randint(1000, 50000)
        trade = HKTrade(
            symbol="0700.HK",
            price=price,
            quantity=quantity,
            timestamp=current_time + pd.Timedelta(minutes=i),
            trade_id=f"trade_{i}",
            buyer_order_id=f"buy_{i}",
            seller_order_id=f"sell_{i}",
            phase=HKTradingPhase.CONTINUOUS_MORNING,
            venue="SEHK"
        )
        analyzer.add_trade(trade)

    # 計算流動性指標
    liquidity_measures = analyzer.calculate_liquidity_measures()
    print("香港市場流動性分析:")
    for metric, value in liquidity_measures.items():
        print(f"  {metric}: {value:.6f}")

if __name__ == "__main__":
    main()