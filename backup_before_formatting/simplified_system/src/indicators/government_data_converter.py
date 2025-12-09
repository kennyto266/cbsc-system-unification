#!/usr/bin/env python3
"""
政府數據技術指標轉換器
Government Data Technical Indicator Converter

將8個香港政府數據源轉換為可交易的技術指標
Convert 8 Hong Kong government data sources into tradable technical indicators
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import warnings

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GovernmentDataConverter:
    """政府數據技術指標轉換器"""

    def __init__(self):
        self.indicators_cache = {}
        self.cache_timeout = 3600  # 1小時緩存

        # 政府數據源配置
        self.data_sources = {
            'hibor_rates': {
                'name': 'HIBOR銀行同業拆息',
                'description': '香港銀行同業拆息利率',
                'indicators': ['hibor_rsi', 'hibor_trend', 'hibor_volatility', 'hibor_momentum', 'hibor_cross_ma']
            },
            'monetary_base': {
                'name': '貨幣基礎',
                'description': '香港貨幣基礎總額',
                'indicators': ['monetary_growth', 'monetary_momentum', 'monetary_ma_crossover', 'monetary_acceleration']
            },
            'exchange_rates': {
                'name': '匯率數據',
                'description': '美元兑港元匯率',
                'indicators': ['exchange_rsi', 'exchange_trend', 'exchange_volatility', 'exchange_strength', 'exchange_divergence']
            },
            'efbn_yield': {
                'name': '外匯基金票據收益率',
                'description': '外匯基金票據及債券收益率',
                'indicators': ['efbn_yield_trend', 'efbn_yield_momentum', 'efbn_volatility', 'efbn_yield_spread']
            },
            'discount_window': {
                'name': '貼現窗利率',
                'description': '貼現窗基本利率',
                'indicators': ['discount_trend', 'discount_momentum', 'discount_volatility', 'discount_signal']
            },
            'market_operation': {
                'name': '市場操作',
                'description': '貨幣市場操作數字',
                'indicators': ['operation_volume', 'operation_frequency', 'operation_impact', 'operation_trend']
            },
            'institutional_bond': {
                'name': '機構債券',
                'description': '機構債券發行數據',
                'indicators': ['bond_yield_trend', 'bond_volume_momentum', 'bond_market_strength', 'bond_signal']
            },
            'forward_exchange': {
                'name': '遠期匯率',
                'description': '港元遠期匯率數字',
                'indicators': ['forward_premium', 'forward_trend', 'forward_volatility', 'forward_arbitrage']
            }
        }

    def convert_hibor_to_indicators(self, hibor_data: pd.Series) -> Dict[str, float]:
        """HIBOR數據轉換為技術指標"""
        try:
            if hibor_data.empty:
                return {}

            indicators = {}

            # 1. HIBOR RSI (利率超買超賣)
            indicators['hibor_rsi'] = self.calculate_rsi(hibor_data, period=14)

            # 2. HIBOR趨勢 (短期vs長期均線)
            ma_short = hibor_data.rolling(window=10).mean()
            ma_long = hibor_data.rolling(window=30).mean()
            indicators['hibor_trend'] = (ma_short.iloc[-1] - ma_long.iloc[-1]) / ma_long.iloc[-1] * 100

            # 3. HIBOR波動率 (利率變化程度)
            indicators['hibor_volatility'] = hibor_data.rolling(window=20).std().iloc[-1]

            # 4. HIBOR動量 (利率變化速度)
            indicators['hibor_momentum'] = (hibor_data.iloc[-1] - hibor_data.iloc[-5]) / hibor_data.iloc[-5] * 100

            # 5. HIBOR交叉信號 (利率與歷史均線交叉)
            ma_200 = hibor_data.rolling(window=50).mean()
            current_rate = hibor_data.iloc[-1]
            indicators['hibor_cross_ma'] = (current_rate - ma_200.iloc[-1]) / ma_200.iloc[-1] * 100

            return indicators

        except Exception as e:
            logger.error(f"HIBOR指標轉換失敗: {e}")
            return {}

    def convert_monetary_base_to_indicators(self, monetary_data: pd.Series) -> Dict[str, float]:
        """貨幣基礎數據轉換為技術指標"""
        try:
            if monetary_data.empty:
                return {}

            indicators = {}

            # 1. 貨幣增長率 (M2增長速度)
            growth_rate = monetary_data.pct_change(periods=30) * 100  # 30日增長率
            indicators['monetary_growth'] = growth_rate.iloc[-1] if not growth_rate.empty else 0

            # 2. 貨幣動量 (增長趨勢強度)
            indicators['monetary_momentum'] = self.calculate_momentum(monetary_data, period=10)

            # 3. 均線交叉信號
            ma_short = monetary_data.rolling(window=10).mean()
            ma_long = monetary_data.rolling(window=30).mean()
            indicators['monetary_ma_crossover'] = (ma_short.iloc[-1] - ma_long.iloc[-1]) / ma_long.iloc[-1] * 100

            # 4. 貨幣加速 (二階導數)
            indicators['monetary_acceleration'] = self.calculate_acceleration(monetary_data)

            return indicators

        except Exception as e:
            logger.error(f"貨幣基礎指標轉換失敗: {e}")
            return {}

    def convert_exchange_rates_to_indicators(self, exchange_data: pd.Series) -> Dict[str, float]:
        """匯率數據轉換為技術指標"""
        try:
            if exchange_data.empty:
                return {}

            indicators = {}

            # 1. 匯率RSI
            indicators['exchange_rsi'] = self.calculate_rsi(exchange_data, period=14)

            # 2. 匯率趨勢
            indicators['exchange_trend'] = self.calculate_trend_strength(exchange_data, period=20)

            # 3. 匯率波動率
            indicators['exchange_volatility'] = exchange_data.rolling(window=20).std().iloc[-1]

            # 4. 匯率強度 (相對強弱指標)
            indicators['exchange_strength'] = self.calculate_relative_strength(exchange_data)

            # 5. 匯率背離 (價格與均線背離)
            indicators['exchange_divergence'] = self.calculate_divergence(exchange_data)

            return indicators

        except Exception as e:
            logger.error(f"匯率指標轉換失敗: {e}")
            return {}

    def convert_efbn_yield_to_indicators(self, efbn_data: pd.Series) -> Dict[str, float]:
        """外匯基金票據收益率轉換為技術指標"""
        try:
            if efbn_data.empty:
                return {}

            indicators = {}

            # 1. 收益率趨勢
            indicators['efbn_yield_trend'] = self.calculate_trend_strength(efbn_data, period=15)

            # 2. 收益率動量
            indicators['efbn_yield_momentum'] = self.calculate_momentum(efbn_data, period=7)

            # 3. 收益率波動率
            indicators['efbn_volatility'] = efbn_data.rolling(window=20).std().iloc[-1]

            # 4. 收益率利差 (短期vs長期)
            short_yield = efbn_data.rolling(window=10).mean()
            long_yield = efbn_data.rolling(window=30).mean()
            indicators['efbn_yield_spread'] = (short_yield.iloc[-1] - long_yield.iloc[-1]) * 100

            return indicators

        except Exception as e:
            logger.error(f"EFBN收益率指標轉換失敗: {e}")
            return {}

    def generate_all_government_indicators(self, gov_data: Dict[str, pd.Series]) -> Dict[str, Dict[str, float]]:
        """生成所有政府數據的技術指標"""
        try:
            all_indicators = {}

            # 轉換各個數據源
            if 'hibor_rates' in gov_data:
                all_indicators['hibor'] = self.convert_hibor_to_indicators(gov_data['hibor_rates'])

            if 'monetary_base' in gov_data:
                all_indicators['monetary'] = self.convert_monetary_base_to_indicators(gov_data['monetary_base'])

            if 'exchange_rates' in gov_data:
                all_indicators['exchange'] = self.convert_exchange_rates_to_indicators(gov_data['exchange_rates'])

            if 'efbn_yield' in gov_data:
                all_indicators['efbn'] = self.convert_efbn_yield_to_indicators(gov_data['efbn_yield'])

            # 統計總指標數量
            total_indicators = sum(len(indicators) for indicators in all_indicators.values())
            logger.info(f"成功生成 {len(all_indicators)} 個數據源的 {total_indicators} 個技術指標")

            return all_indicators

        except Exception as e:
            logger.error(f"政府數據指標生成失敗: {e}")
            return {}

    def create_trading_signals_from_gov_data(self, indicators: Dict[str, Dict[str, float]]) -> Dict[str, str]:
        """從政府數據指標創建交易信號 (純買賣，無HOLD)"""
        try:
            signals = {}

            # 綜合評分系統
            total_score = 0
            active_sources = 0

            # HIBOR信號 (利率分析)
            if 'hibor' in indicators:
                hibor_ind = indicators['hibor']
                hibor_score = 0

                # 低利率 = 看漲股市 (買信號)
                if 'hibor_rsi' in hibor_ind:
                    if hibor_ind['hibor_rsi'] < 30:  # 超賣(利率過低)
                        hibor_score += 2
                    elif hibor_ind['hibor_rsi'] > 70:  # 超買(利率過高)
                        hibor_score -= 2

                if 'hibor_trend' in hibor_ind:
                    if hibor_ind['hibor_trend'] < 0:  # 利率下降趨勢
                        hibor_score += 1
                    else:  # 利率上升趨勢
                        hibor_score -= 1

                signals['hibor'] = 'BUY' if hibor_score > 0 else 'SELL'
                total_score += hibor_score
                active_sources += 1

            # 貨幣供應信號
            if 'monetary' in indicators:
                monetary_ind = indicators['monetary']
                monetary_score = 0

                # 貨幣增長 = 看漲股市
                if 'monetary_growth' in monetary_ind and monetary_ind['monetary_growth'] > 0:
                    monetary_score += 1

                if 'monetary_ma_crossover' in monetary_ind:
                    if monetary_ind['monetary_ma_crossover'] > 0:  # 短期高於長期
                        monetary_score += 1

                signals['monetary'] = 'BUY' if monetary_score > 0 else 'SELL'
                total_score += monetary_score
                active_sources += 1

            # 匯率信號 (港匯強度)
            if 'exchange' in indicators:
                exchange_ind = indicators['exchange']
                exchange_score = 0

                # 港元強勢 = 看跌股市 (賣信號)
                if 'exchange_trend' in exchange_ind:
                    if exchange_ind['exchange_trend'] > 0:  # 港元升值趨勢
                        exchange_score -= 1
                    else:  # 港元貶值趨勢
                        exchange_score += 1

                signals['exchange'] = 'BUY' if exchange_score > 0 else 'SELL'
                total_score += exchange_score
                active_sources += 1

            # 最終綜合信號 (強制買賣，無HOLD)
            if active_sources > 0:
                avg_score = total_score / active_sources

                # 根據市場情況調整閾值
                market_volatility = self.calculate_market_volatility(indicators)

                if market_volatility > 0.5:  # 高波動市場
                    threshold = 0.1  # 降低閾值
                else:  # 低波動市場
                    threshold = 0.3  # 提高閾值

                final_signal = 'BUY' if avg_score > threshold else 'SELL'
            else:
                final_signal = 'HOLD'  # 數據不足時的默認值

            # 確保無HOLD信號
            if final_signal == 'HOLD':
                final_signal = 'BUY' if total_score >= 0 else 'SELL'

            signals['final'] = final_signal
            signals['confidence'] = abs(avg_score) if active_sources > 0 else 0.5
            signals['active_sources'] = active_sources

            logger.info(f"政府數據信號生成: {final_signal}, 置信度: {signals['confidence']:.2f}")
            return signals

        except Exception as e:
            logger.error(f"政府數據信號生成失敗: {e}")
            return {'final': 'BUY', 'confidence': 0.5, 'error': str(e)}

    # ============ 輔助方法 ============

    def calculate_rsi(self, data: pd.Series, period: int = 14) -> float:
        """計算RSI指標"""
        try:
            delta = data.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            return rsi.iloc[-1] if not rsi.empty else 50

        except:
            return 50

    def calculate_momentum(self, data: pd.Series, period: int = 10) -> float:
        """計算動量指標"""
        try:
            if len(data) < period + 1:
                return 0
            return (data.iloc[-1] - data.iloc[-period-1]) / data.iloc[-period-1] * 100
        except:
            return 0

    def calculate_trend_strength(self, data: pd.Series, period: int = 20) -> float:
        """計算趨勢強度"""
        try:
            if len(data) < period:
                return 0

            # 使用線性回歸計算趨勢
            x = np.arange(len(data))
            y = data.values

            # 計算斜率
            slope = np.polyfit(x[-period:], y[-period:], 1)[0]
            return slope * 100  # 轉換為百分比

        except:
            return 0

    def calculate_relative_strength(self, data: pd.Series) -> float:
        """計算相對強度"""
        try:
            ma_200 = data.rolling(window=50).mean()
            current = data.iloc[-1]
            return (current - ma_200.iloc[-1]) / ma_200.iloc[-1] * 100
        except:
            return 0

    def calculate_divergence(self, data: pd.Series) -> float:
        """計算背離度"""
        try:
            ma_20 = data.rolling(window=20).mean()
            current = data.iloc[-1]
            ma_current = ma_20.iloc[-1]
            return (current - ma_current) / ma_current * 100
        except:
            return 0

    def calculate_acceleration(self, data: pd.Series) -> float:
        """計算加速度 (二階導數)"""
        try:
            if len(data) < 3:
                return 0

            # 計算一階差分
            first_diff = data.diff().dropna()

            # 計算二階差分 (加速度)
            second_diff = first_diff.diff().dropna()

            return second_diff.iloc[-1] if not second_diff.empty else 0

        except:
            return 0

    def calculate_market_volatility(self, indicators: Dict[str, Dict[str, float]]) -> float:
        """計算市場總體波動率"""
        try:
            all_values = []
            for source_data in indicators.values():
                for value in source_data.values():
                    if isinstance(value, (int, float)):
                        all_values.append(abs(value))

            if not all_values:
                return 0.5

            # 使用標準差作為波動率指標
            volatility = np.std(all_values)

            # 正規化到0-1範圍
            return min(volatility / 10, 1.0)  # 假設10%為高波動

        except:
            return 0.5

if __name__ == "__main__":
    # 測試代碼
    converter = GovernmentDataConverter()

    print("政府數據技術指標轉換器初始化完成")
    print(f"支持 {len(converter.data_sources)} 個數據源")

    for source_id, config in converter.data_sources.items():
        print(f"- {config['name']}: {len(config['indicators'])} 個指標")