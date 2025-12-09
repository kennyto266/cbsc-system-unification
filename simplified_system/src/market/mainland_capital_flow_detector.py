#!/usr/bin/env python3
"""
內地資金流動檢測系統 - Mainland Capital Flow Detection System
監測和分析內地南向資金流入香港市場的動向
Mainland Capital Flow Detection - Monitoring and analyzing Mainland southbound capital flows to Hong Kong market
"""

import asyncio
import aiohttp
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import pandas as pd
import numpy as np
from pathlib import Path
import pickle
import statistics

# Setup logging
logger = logging.getLogger(__name__)

class CapitalFlowType(Enum):
    """資金流動類型"""
    SOUTHBOUND_BUY = "southbound_buy"        # 南向買入
    SOUTHBOUND_SELL = "southbound_sell"      # 南向賣出
    NORTHBOUND_BUY = "northbound_buy"        # 北向買入
    NORTHBOUND_SELL = "northbound_sell"      # 北向賣出
    A_SHARE_HK_BUY = "a_share_hk_buy"        # A+H股套利買入
    A_SHARE_HK_SELL = "a_share_hk_sell"      # A+H股套利賣出

class FlowIntensity(Enum):
    """流動強度"""
    MINIMAL = "minimal"      # < 1億港元
    LOW = "low"             # 1-5億港元
    MODERATE = "moderate"    # 5-20億港元
    HIGH = "high"           # 20-50億港元
    VERY_HIGH = "very_high" # > 50億港元

class FlowSentiment(Enum):
    """資金情緒"""
    STRONGLY_BEARISH = "strongly_bearish"  # 淨流出 > 20億
    BEARISH = "bearish"                     # 淨流出 5-20億
    NEUTRAL = "neutral"                     # 浮動 +/- 5億
    BULLISH = "bullish"                     # 淨流入 5-20億
    STRONGLY_BULLISH = "strongly_bullish"  # 淨流入 > 20億

@dataclass
class CapitalFlowData:
    """資金流動數據"""
    timestamp: datetime
    flow_type: CapitalFlowType
    amount_hkd: float
    volume_shares: float
    target_symbols: List[str]
    source_exchanges: List[str]
    transaction_count: int

@dataclass
class SectorFlowAnalysis:
    """行業資金流動分析"""
    sector: str
    net_flow_hkd: float
    flow_intensity: FlowIntensity
    top_gainers: List[str]
    top_losers: List[str]
    momentum_score: float
    valuation_impact: float

@dataclass
class MainlandCapitalFlowReport:
    """內地資金流動報告"""
    timestamp: datetime
    total_southbound_flow: float
    total_northbound_flow: float
    net_flow: float
    flow_sentiment: FlowSentiment
    sector_analyses: Dict[str, SectorFlowAnalysis]
    top_flow_symbols: List[Dict[str, Any]]
    market_impact_assessment: Dict[str, float]
    trend_analysis: Dict[str, Any]
    risk_indicators: List[str]

class MainlandCapitalFlowDataFetcher:
    """內地資金流動數據獲取器"""

    def __init__(self):
        self.data_sources = {
            "hkma_southbound": "https://www.hkex.com.hk/eng/csm/SouthBoundData.asp",
            "hkma_connect": "https://www.hkex.com.hk/eng/csm/DailyStat.asp",
            "wind_southbound": "https://api.wind.com.cn/v1/edb",  # 萬得API
            "ceic_data": "https://insights.ceicdata.com/api/v1",  # CEIC數據
        }
        self.session = None
        self.cache = {}
        self.cache_ttl = 300  # 5分鐘緩存

    async def fetch_southbound_data(self) -> List[CapitalFlowData]:
        """獲取南向資金數據"""
        cache_key = "southbound_data"

        # 檢查緩存
        if cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if datetime.now() - timestamp < timedelta(seconds=self.cache_ttl):
                return cached_data

        try:
            # 嘗試獲取真實數據
            real_data = await self._fetch_real_southbound_data()
            if real_data:
                self.cache[cache_key] = (real_data, datetime.now())
                return real_data
        except Exception as e:
            logger.warning(f"Failed to fetch real southbound data: {e}")

        # 使用模擬數據
        mock_data = self._generate_mock_southbound_data()
        self.cache[cache_key] = (mock_data, datetime.now())
        return mock_data

    async def _fetch_real_southbound_data(self) -> Optional[List[CapitalFlowData]]:
        """獲取真實南向資金數據"""
        try:
            async with aiohttp.ClientSession() as session:
                # 香港交易所南向資金數據
                url = "https://www.hkex.com.hk/eng/stat/dmstat/daystat/dmstat.htm"

                # 模擬API調用（實際需要解析網頁或使用專業API）
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }

                # 這裡需要實現真實的數據解析邏輯
                # 暫時返回None使用模擬數據
                return None

        except Exception as e:
            logger.error(f"Error fetching real southbound data: {e}")
            return None

    def _generate_mock_southbound_data(self) -> List[CapitalFlowData]:
        """生成模擬南向資金數據"""
        current_time = datetime.now()
        mock_data = []

        # 模擬過去30天的數據
        for i in range(30):
            date = current_time - timedelta(days=i)

            # 基礎南向資金規模（億港元）
            base_flow = np.random.normal(15, 5)  # 平均15億，標準差5億
            base_flow = max(0, base_flow)  # 不能為負

            # 模擬買入和賣出
            buy_amount = base_flow * np.random.uniform(0.6, 0.9)
            sell_amount = base_flow * np.random.uniform(0.1, 0.4)

            # 模擬目標股票（主要HSI成分股）
            target_symbols = np.random.choice([
                "0700.HK", "0941.HK", "1299.HK", "2318.HK", "0388.HK",
                "09988.HK", "0005.HK", "1398.HK", "2628.HK", "3988.HK"
            ], size=np.random.randint(3, 8), replace=False).tolist()

            mock_data.append(CapitalFlowData(
                timestamp=date,
                flow_type=CapitalFlowType.SOUTHBOUND_BUY,
                amount_hkd=buy_amount * 100000000,  # 轉換為港元
                volume_shares=buy_amount * 1000000 / 300,  # 假設平均股價300港元
                target_symbols=target_symbols,
                source_exchanges=["Shanghai", "Shenzhen", "Beijing"],
                transaction_count=int(buy_amount * 50)  # 每億港元50筆交易
            ))

            mock_data.append(CapitalFlowData(
                timestamp=date,
                flow_type=CapitalFlowType.SOUTHBOUND_SELL,
                amount_hkd=sell_amount * 100000000,
                volume_shares=sell_amount * 1000000 / 300,
                target_symbols=target_symbols[:3],  # 賣出通常集中在少數股票
                source_exchanges=["Shanghai", "Shenzhen"],
                transaction_count=int(sell_amount * 30)
            ))

        return mock_data

class MainlandCapitalFlowAnalyzer:
    """內地資金流動分析器"""

    def __init__(self):
        self.data_fetcher = MainlandCapitalFlowDataFetcher()

        # 行業分類映射
        self.sector_mapping = {
            "金融": ["0388.HK", "0005.HK", "1398.HK", "3988.HK", "2318.HK", "1299.HK", "2628.HK"],
            "科技": ["0700.HK", "09988.HK", "09618.HK"],
            "電信": ["0941.HK"],
            "公用事業": ["0002.HK"],
            "消費": ["09918.HK", "00775.HK"],
            "ETF": ["02800.HK", "02833.HK"]
        }

        # A+H股映射
        self.ah_stock_mapping = {
            "0700.HK": "00700.HK",  # 騰訊
            "0941.HK": "00941.HK",  # 中國移動
            "1398.HK": "01398.HK",  # 工商銀行
            "3988.HK": "03988.HK",  # 中國銀行
            "2318.HK": "02318.HK",  # 中國平安
        }

    async def generate_capital_flow_report(self) -> MainlandCapitalFlowReport:
        """生成資金流動報告"""
        # 獲取資金流動數據
        flow_data = await self.data_fetcher.fetch_southbound_data()

        # 計算總體資金流動
        total_southbound, total_northbound, net_flow = self._calculate_total_flows(flow_data)

        # 判斷資金情緒
        flow_sentiment = self._determine_flow_sentiment(net_flow)

        # 行業資金流動分析
        sector_analyses = await self._analyze_sector_flows(flow_data)

        # 熱門資金流向股票
        top_flow_symbols = self._identify_top_flow_symbols(flow_data)

        # 市場影響評估
        market_impact = self._assess_market_impact(flow_data, net_flow)

        # 趨勢分析
        trend_analysis = self._analyze_flow_trends(flow_data)

        # 風險指標
        risk_indicators = self._generate_risk_indicators(flow_data, net_flow)

        return MainlandCapitalFlowReport(
            timestamp=datetime.now(),
            total_southbound_flow=total_southbound,
            total_northbound_flow=total_northbound,
            net_flow=net_flow,
            flow_sentiment=flow_sentiment,
            sector_analyses=sector_analyses,
            top_flow_symbols=top_flow_symbols,
            market_impact_assessment=market_impact,
            trend_analysis=trend_analysis,
            risk_indicators=risk_indicators
        )

    def _calculate_total_flows(self, flow_data: List[CapitalFlowData]) -> Tuple[float, float, float]:
        """計算總體資金流動"""
        southbound_buy = sum(d.amount_hkd for d in flow_data if d.flow_type == CapitalFlowType.SOUTHBOUND_BUY)
        southbound_sell = sum(d.amount_hkd for d in flow_data if d.flow_type == CapitalFlowType.SOUTHBOUND_SELL)

        total_southbound = southbound_buy - southbound_sell

        # 北向資金模擬（通常較小）
        total_northbound = -total_southbound * np.random.uniform(0.3, 0.7)

        net_flow = total_southbound + total_northbound

        return total_southbound, total_northbound, net_flow

    def _determine_flow_sentiment(self, net_flow: float) -> FlowSentiment:
        """判斷資金情緒"""
        net_flow_billion = net_flow / 1000000000  # 轉換為億港元

        if net_flow_billion > 20:
            return FlowSentiment.STRONGLY_BULLISH
        elif net_flow_billion > 5:
            return FlowSentiment.BULLISH
        elif net_flow_billion > -5:
            return FlowSentiment.NEUTRAL
        elif net_flow_billion > -20:
            return FlowSentiment.BEARISH
        else:
            return FlowSentiment.STRONGLY_BEARISH

    async def _analyze_sector_flows(self, flow_data: List[CapitalFlowData]) -> Dict[str, SectorFlowAnalysis]:
        """分析行業資金流動"""
        sector_flows = {}

        # 初始化行業資金統計
        for sector in self.sector_mapping.keys():
            sector_flows[sector] = {
                'buy_flow': 0,
                'sell_flow': 0,
                'symbols': {},
                'transaction_count': 0
            }

        # 統計每個行業的資金流動
        for flow in flow_data:
            if flow.flow_type in [CapitalFlowType.SOUTHBOUND_BUY, CapitalFlowType.SOUTHBOUND_SELL]:
                amount = flow.amount_hkd if flow.flow_type == CapitalFlowType.SOUTHBOUND_BUY else -flow.amount_hkd

                for symbol in flow.target_symbols:
                    sector = self._get_symbol_sector(symbol)
                    if sector:
                        if flow.flow_type == CapitalFlowType.SOUTHBOUND_BUY:
                            sector_flows[sector]['buy_flow'] += amount / len(flow.target_symbols)
                        else:
                            sector_flows[sector]['sell_flow'] += abs(amount / len(flow.target_symbols))

                        if symbol not in sector_flows[sector]['symbols']:
                            sector_flows[sector]['symbols'][symbol] = 0
                        sector_flows[sector]['symbols'][symbol] += amount / len(flow.target_symbols)

                        sector_flows[sector]['transaction_count'] += flow.transaction_count

        # 生成行業分析
        sector_analyses = {}
        for sector, stats in sector_flows.items():
            net_flow = stats['buy_flow'] - stats['sell_flow']
            total_flow = stats['buy_flow'] + stats['sell_flow']

            # 確定流動強度
            flow_intensity = self._determine_flow_intensity(total_flow / 100000000)  # 轉換為億港元

            # 計算動量分數
            momentum_score = self._calculate_momentum_score(stats['symbols'])

            # 評估值影響
            valuation_impact = self._assess_valuation_impact(sector, net_flow)

            # 找出漲跌最多的股票
            symbol_flows = stats['symbols']
            sorted_symbols = sorted(symbol_flows.items(), key=lambda x: x[1], reverse=True)

            top_gainers = [symbol for symbol, flow in sorted_symbols[:3] if flow > 0]
            top_losers = [symbol for symbol, flow in sorted_symbols[-3:] if flow < 0]

            sector_analyses[sector] = SectorFlowAnalysis(
                sector=sector,
                net_flow_hkd=net_flow,
                flow_intensity=flow_intensity,
                top_gainers=top_gainers,
                top_losers=top_losers,
                momentum_score=momentum_score,
                valuation_impact=valuation_impact
            )

        return sector_analyses

    def _get_symbol_sector(self, symbol: str) -> Optional[str]:
        """獲取股票所屬行業"""
        for sector, symbols in self.sector_mapping.items():
            if symbol in symbols:
                return sector
        return None

    def _determine_flow_intensity(self, flow_billion: float) -> FlowIntensity:
        """確定資金流動強度"""
        if flow_billion < 1:
            return FlowIntensity.MINIMAL
        elif flow_billion < 5:
            return FlowIntensity.LOW
        elif flow_billion < 20:
            return FlowIntensity.MODERATE
        elif flow_billion < 50:
            return FlowIntensity.HIGH
        else:
            return FlowIntensity.VERY_HIGH

    def _calculate_momentum_score(self, symbol_flows: Dict[str, float]) -> float:
        """計算動量分數"""
        if not symbol_flows:
            return 0.0

        flows = list(symbol_flows.values())
        positive_flows = sum(f for f in flows if f > 0)
        negative_flows = sum(abs(f) for f in flows if f < 0)
        total_flows = positive_flows + negative_flows

        if total_flows == 0:
            return 0.0

        # 動量分數 = (淨流入 - 淨流出) / 總流動
        momentum = (positive_flows - negative_flows) / total_flows
        return max(-1.0, min(1.0, momentum))

    def _assess_valuation_impact(self, sector: str, net_flow: float) -> float:
        """評估對估值的影響"""
        # 不同行業對資金流動的敏感度不同
        sector_sensitivity = {
            "金融": 0.3,      # 金融股相對穩定
            "科技": 0.8,      # 科技股對資金敏感
            "電信": 0.4,      # 電信股中等敏感
            "公用事業": 0.2,  # 公用事業較穩定
            "消費": 0.6,      # 消費股較敏感
            "ETF": 0.5,       # ETF中等敏感
        }

        sensitivity = sector_sensitivity.get(sector, 0.5)

        # 資金流動影響（億港元）
        flow_billion = abs(net_flow) / 1000000000

        # 影響 = 敏感度 * log(資金規模 + 1)
        impact = sensitivity * np.log(flow_billion + 1) * 0.01

        if net_flow < 0:
            impact = -impact

        return round(impact, 3)

    def _identify_top_flow_symbols(self, flow_data: List[CapitalFlowData]) -> List[Dict[str, Any]]:
        """識別資金流動最活躍的股票"""
        symbol_flows = {}

        # 統計每隻股票的資金淨流入
        for flow in flow_data:
            if flow.flow_type in [CapitalFlowType.SOUTHBOUND_BUY, CapitalFlowType.SOUTHBOUND_SELL]:
                amount = flow.amount_hkd if flow.flow_type == CapitalFlowType.SOUTHBOUND_BUY else -flow.amount_hkd

                per_symbol_amount = amount / len(flow.target_symbols)
                for symbol in flow.target_symbols:
                    if symbol not in symbol_flows:
                        symbol_flows[symbol] = {
                            'net_flow': 0,
                            'buy_volume': 0,
                            'sell_volume': 0,
                            'transaction_count': 0,
                            'first_seen': flow.timestamp,
                            'last_seen': flow.timestamp
                        }

                    if flow.flow_type == CapitalFlowType.SOUTHBOUND_BUY:
                        symbol_flows[symbol]['buy_volume'] += per_symbol_amount
                    else:
                        symbol_flows[symbol]['sell_volume'] += abs(per_symbol_amount)

                    symbol_flows[symbol]['net_flow'] += per_symbol_amount
                    symbol_flows[symbol]['transaction_count'] += flow.transaction_count
                    symbol_flows[symbol]['last_seen'] = max(
                        symbol_flows[symbol]['last_seen'], flow.timestamp
                    )

        # 排序並返回前10名
        sorted_symbols = sorted(
            symbol_flows.items(),
            key=lambda x: abs(x[1]['net_flow']),
            reverse=True
        )[:10]

        result = []
        for symbol, stats in sorted_symbols:
            result.append({
                'symbol': symbol,
                'sector': self._get_symbol_sector(symbol),
                'net_flow_hkd': stats['net_flow'],
                'buy_volume_hkd': stats['buy_volume'],
                'sell_volume_hkd': stats['sell_volume'],
                'transaction_count': stats['transaction_count'],
                'is_ah_stock': symbol in self.ah_stock_mapping,
                'momentum_score': stats['net_flow'] / (stats['buy_volume'] + stats['sell_volume']) if (stats['buy_volume'] + stats['sell_volume']) > 0 else 0
            })

        return result

    def _assess_market_impact(self, flow_data: List[CapitalFlowData], net_flow: float) -> Dict[str, float]:
        """評估對市場的影響"""
        # 計算資金流動變化率
        if len(flow_data) < 2:
            return {
                'market_liquidity_impact': 0.0,
                'price_pressure': 0.0,
                'volatility_impact': 0.0,
                'sector_rotation_indicator': 0.0
            }

        # 按日期分組計算日淨流入
        daily_flows = {}
        for flow in flow_data:
            date_key = flow.timestamp.date()
            if date_key not in daily_flows:
                daily_flows[date_key] = 0

            if flow.flow_type == CapitalFlowType.SOUTHBOUND_BUY:
                daily_flows[date_key] += flow.amount_hkd
            elif flow.flow_type == CapitalFlowType.SOUTHBOUND_SELL:
                daily_flows[date_key] -= flow.amount_hkd

        if len(daily_flows) < 2:
            return {
                'market_liquidity_impact': 0.0,
                'price_pressure': 0.0,
                'volatility_impact': 0.0,
                'sector_rotation_indicator': 0.0
            }

        # 計算趨勢和變化率
        sorted_dates = sorted(daily_flows.keys())
        recent_flows = [daily_flows[date] for date in sorted_dates[-5:]]  # 最近5天
        earlier_flows = [daily_flows[date] for date in sorted_dates[-10:-5]] if len(sorted_dates) >= 10 else recent_flows[:len(recent_flows)]

        recent_avg = np.mean(recent_flows) if recent_flows else 0
        earlier_avg = np.mean(earlier_flows) if earlier_flows else recent_avg

        # 影響評估
        net_flow_billion = net_flow / 1000000000
        flow_change_rate = (recent_avg - earlier_avg) / abs(earlier_avg) if earlier_avg != 0 else 0

        return {
            'market_liquidity_impact': min(1.0, abs(net_flow_billion) / 50),  # 50億港元為滿分影響
            'price_pressure': np.sign(net_flow) * min(0.2, abs(net_flow_billion) / 100),  # 最大20%價格壓力
            'volatility_impact': abs(flow_change_rate) * 0.1,  # 流動變化影響波動率
            'sector_rotation_indicator': self._calculate_sector_rotation_indicator(flow_data)
        }

    def _calculate_sector_rotation_indicator(self, flow_data: List[CapitalFlowData]) -> float:
        """計算行業輪動指標"""
        sector_daily_flows = {}

        # 計算各行業的日淨流入
        for flow in flow_data:
            if flow.flow_type not in [CapitalFlowType.SOUTHBOUND_BUY, CapitalFlowType.SOUTHBOUND_SELL]:
                continue

            date_key = flow.timestamp.date()
            if date_key not in sector_daily_flows:
                sector_daily_flows[date_key] = {}

            amount = flow.amount_hkd if flow.flow_type == CapitalFlowType.SOUTHBOUND_BUY else -flow.amount_hkd
            per_symbol_amount = amount / len(flow.target_symbols)

            for symbol in flow.target_symbols:
                sector = self._get_symbol_sector(symbol)
                if sector:
                    if sector not in sector_daily_flows[date_key]:
                        sector_daily_flows[date_key][sector] = 0
                    sector_daily_flows[date_key][sector] += per_symbol_amount

        if len(sector_daily_flows) < 2:
            return 0.0

        # 計算行業資金排名的變化
        dates = sorted(sector_daily_flows.keys())
        latest_date = dates[-1]
        previous_date = dates[-2] if len(dates) >= 2 else latest_date

        latest_rankings = sorted(
            [(sector, flow) for sector, flow in sector_daily_flows[latest_date].items()],
            key=lambda x: x[1],
            reverse=True
        )

        if previous_date in sector_daily_flows:
            previous_rankings = sorted(
                [(sector, flow) for sector, flow in sector_daily_flows[previous_date].items()],
                key=lambda x: x[1],
                reverse=True
            )

            # 計算排名變化
            rank_changes = 0
            for i, (sector, _) in enumerate(latest_rankings):
                prev_rank = next((j for j, (prev_sector, _) in enumerate(previous_rankings) if prev_sector == sector), i)
                rank_changes += abs(i - prev_rank)

            # 輪動指標 = 排名變化 / 最大可能變化
            max_changes = len(latest_rankings) * (len(latest_rankings) - 1) / 2
            return rank_changes / max_changes if max_changes > 0 else 0.0

        return 0.0

    def _analyze_flow_trends(self, flow_data: List[CapitalFlowData]) -> Dict[str, Any]:
        """分析資金流動趨勢"""
        # 按日期分組
        daily_flows = {}
        daily_transaction_counts = {}

        for flow in flow_data:
            date_key = flow.timestamp.date()
            if date_key not in daily_flows:
                daily_flows[date_key] = 0
                daily_transaction_counts[date_key] = 0

            if flow.flow_type == CapitalFlowType.SOUTHBOUND_BUY:
                daily_flows[date_key] += flow.amount_hkd
            elif flow.flow_type == CapitalFlowType.SOUTHBOUND_SELL:
                daily_flows[date_key] -= flow.amount_hkd

            daily_transaction_counts[date_key] += flow.transaction_count

        if len(daily_flows) < 3:
            return {
                'short_term_trend': 'insufficient_data',
                'medium_term_trend': 'insufficient_data',
                'momentum_strength': 0.0,
                'consistency_score': 0.0,
                'recent_acceleration': 0.0
            }

        # 計算趨勢
        sorted_dates = sorted(daily_flows.keys())
        flows = [daily_flows[date] / 1000000000 for date in sorted_dates]  # 轉換為億港元

        # 短期趨勢（最近3天）
        short_trend = self._calculate_trend_direction(flows[-3:])

        # 中期趨勢（最近7天）
        medium_trend = self._calculate_trend_direction(flows[-7:]) if len(flows) >= 7 else short_trend

        # 動量強度
        momentum_strength = self._calculate_momentum_strength(flows)

        # 一致性分數
        consistency_score = self._calculate_consistency_score(flows)

        # 近期加速度
        recent_acceleration = self._calculate_acceleration(flows)

        return {
            'short_term_trend': short_trend,
            'medium_term_trend': medium_trend,
            'momentum_strength': momentum_strength,
            'consistency_score': consistency_score,
            'recent_acceleration': recent_acceleration,
            'average_daily_flow_billion': np.mean(flows),
            'flow_volatility': np.std(flows),
            'total_transaction_count': sum(daily_transaction_counts.values())
        }

    def _calculate_trend_direction(self, values: List[float]) -> str:
        """計算趨勢方向"""
        if len(values) < 2:
            return 'insufficient_data'

        # 使用線性回歸計算趨勢
        x = np.arange(len(values))
        if len(values) > 1 and np.std(values) > 0:
            slope = np.polyfit(x, values, 1)[0]

            if slope > 0.1:
                return 'strong_uptrend'
            elif slope > 0.01:
                return 'uptrend'
            elif slope < -0.1:
                return 'strong_downtrend'
            elif slope < -0.01:
                return 'downtrend'
            else:
                return 'sideways'
        else:
            return 'stable'

    def _calculate_momentum_strength(self, values: List[float]) -> float:
        """計算動量強度"""
        if len(values) < 3:
            return 0.0

        # 計算最近值相比平均值的偏差
        recent_values = values[-3:]
        historical_mean = np.mean(values[:-3]) if len(values) > 3 else np.mean(values)
        recent_mean = np.mean(recent_values)

        momentum = (recent_mean - historical_mean) / (abs(historical_mean) + 1e-6)
        return max(-1.0, min(1.0, momentum))

    def _calculate_consistency_score(self, values: List[float]) -> float:
        """計算一致性分數"""
        if len(values) < 2:
            return 0.0

        # 計算正流動天數比例
        positive_days = sum(1 for v in values if v > 0)
        consistency = positive_days / len(values)

        # 調整：如果平均值為正，給予額外分數
        avg_value = np.mean(values)
        if avg_value > 0:
            consistency = consistency * 0.7 + 0.3

        return max(0.0, min(1.0, consistency))

    def _calculate_acceleration(self, values: List[float]) -> float:
        """計算加速度"""
        if len(values) < 4:
            return 0.0

        # 計算最近期和之前期的變化率
        recent_change = values[-1] - values[-2]
        previous_change = values[-2] - values[-3]

        # 加速度 = 最近變化率 - 之前變化率
        acceleration = recent_change - previous_change

        # 標準化
        avg_change = np.mean([abs(values[i] - values[i-1]) for i in range(1, len(values))])
        if avg_change > 0:
            return acceleration / avg_change
        else:
            return 0.0

    def _generate_risk_indicators(self, flow_data: List[CapitalFlowData], net_flow: float) -> List[str]:
        """生成風險指標"""
        indicators = []

        net_flow_billion = net_flow / 1000000000

        # 資金流向風險
        if net_flow_billion < -30:
            indicators.append("大規模資金外流風險")
        elif net_flow_billion < -10:
            indicators.append("資金流出壓力")
        elif net_flow_billion > 50:
            indicators.append("過熱資金流入風險")

        # 交易集中度風險
        symbol_concentration = self._calculate_concentration_risk(flow_data)
        if symbol_concentration > 0.7:
            indicators.append("股票集中度風險")

        # 行業集中度風險
        sector_concentration = self._calculate_sector_concentration_risk(flow_data)
        if sector_concentration > 0.6:
            indicators.append("行業集中度風險")

        # 流動性風險
        if abs(net_flow_billion) > 20:
            indicators.append("市場流動性影響風險")

        return indicators

    def _calculate_concentration_risk(self, flow_data: List[CapitalFlowData]) -> float:
        """計算股票集中度風險"""
        symbol_flows = {}
        total_flow = 0

        for flow in flow_data:
            if flow.flow_type in [CapitalFlowType.SOUTHBOUND_BUY, CapitalFlowType.SOUTHBOUND_SELL]:
                amount = abs(flow.amount_hkd)
                total_flow += amount

                per_symbol_amount = amount / len(flow.target_symbols)
                for symbol in flow.target_symbols:
                    if symbol not in symbol_flows:
                        symbol_flows[symbol] = 0
                    symbol_flows[symbol] += per_symbol_amount

        if total_flow == 0 or not symbol_flows:
            return 0.0

        # 計算赫芬達爾指數
        top_10_flows = sorted(symbol_flows.values(), reverse=True)[:10]
        concentration = sum((flow / total_flow) ** 2 for flow in top_10_flows)

        return concentration

    def _calculate_sector_concentration_risk(self, flow_data: List[CapitalFlowData]) -> float:
        """計算行業集中度風險"""
        sector_flows = {}
        total_flow = 0

        for flow in flow_data:
            if flow.flow_type not in [CapitalFlowType.SOUTHBOUND_BUY, CapitalFlowType.SOUTHBOUND_SELL]:
                continue

            amount = abs(flow.amount_hkd)
            total_flow += amount

            per_symbol_amount = amount / len(flow.target_symbols)
            for symbol in flow.target_symbols:
                sector = self._get_symbol_sector(symbol)
                if sector:
                    if sector not in sector_flows:
                        sector_flows[sector] = 0
                    sector_flows[sector] += per_symbol_amount

        if total_flow == 0 or not sector_flows:
            return 0.0

        # 計算行業集中度
        concentration = sum((flow / total_flow) ** 2 for flow in sector_flows.values())

        return concentration

# 全局實例
_flow_detector = None

def get_mainland_capital_flow_detector() -> MainlandCapitalFlowAnalyzer:
    """獲取內地資金流動檢測器單例"""
    global _flow_detector
    if _flow_detector is None:
        _flow_detector = MainlandCapitalFlowAnalyzer()
    return _flow_detector

# 使用示例
async def example_capital_flow_analysis():
    """資金流動分析示例"""
    detector = get_mainland_capital_flow_detector()

    try:
        # 生成資金流動報告
        report = await detector.generate_capital_flow_report()

        print("Mainland Capital Flow Report:")
        print(f"Net Flow: {report.net_flow / 1000000000:.2f} billion HKD")
        print(f"Sentiment: {report.flow_sentiment.value}")
        print(f"Top Flow Symbols: {len(report.top_flow_symbols)}")

        print("\nSector Analysis:")
        for sector, analysis in report.sector_analyses.items():
            print(f"  {sector}: {analysis.net_flow_hkd / 1000000000:.2f}B HKD ({analysis.flow_intensity.value})")

        print(f"\nRisk Indicators: {report.risk_indicators}")

    except Exception as e:
        print(f"Capital flow analysis failed: {e}")

if __name__ == "__main__":
    asyncio.run(example_capital_flow_analysis())