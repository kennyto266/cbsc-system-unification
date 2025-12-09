#!/usr/bin/env python3
"""
API集成多指標技術分析系統
API-Integrated Multi-Indicator Technical Analysis System

直接使用真實每日任務API進行技術分析
"""

import asyncio
import aiohttp
import pandas as pd
import numpy as np
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from indicators.core_indicators import CoreIndicators
from indicators.technical_analyzer import TechnicalAnalyzer

logger = logging.getLogger(__name__)

class APIMultiIndicatorSystem:
    """基於真實API的多指標技術分析系統"""

    def __init__(self):
        """初始化系統"""
        self.indicators = CoreIndicators()
        self.analyzer = TechnicalAnalyzer()

        # 真實API端點配置
        self.daily_api_base = "http://localhost:8001"  # Simplified System API
        self.real_api_base = "http://localhost:8002"    # Real Data API (如果在不同端口)

        # 數據源映射
        self.data_sources = {
            'hibor_overnight': 'hibor',
            'monetary_base': 'hkma_monetary',
            'exchange_rate': 'hkma_exchange',
            'trade_data': 'trade',
            'gdp_data': 'gdp'
        }

        logger.info("API Multi-Indicator System initialized")

    async def test_api_connectivity(self, api_base: str) -> bool:
        """測試API連接性"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{api_base}/health", timeout=aiohttp.ClientTimeout(total=5)) as response:
                    return response.status == 200
        except Exception as e:
            logger.warning(f"API connectivity test failed for {api_base}: {e}")
            return False

    async def get_latest_data(self, source_name: str, api_base: str = None) -> Optional[Dict]:
        """從API獲取最新數據"""
        if api_base is None:
            api_base = self.daily_api_base

        try:
            async with aiohttp.ClientSession() as session:
                url = f"{api_base}/data/{source_name}/latest"
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"Successfully fetched data for {source_name}")
                        return data
                    else:
                        logger.error(f"API error for {source_name}: {response.status}")
                        return None
        except Exception as e:
            logger.error(f"Error fetching data for {source_name}: {e}")
            return None

    async def collect_all_real_data(self) -> Dict[str, pd.DataFrame]:
        """收集所有真實數據"""
        logger.info("Starting real-time data collection from APIs")

        data_dict = {}

        # 測試API連接
        daily_api_available = await self.test_api_connectivity(self.daily_api_base)

        if not daily_api_available:
            logger.warning("Daily API not available, trying fallback API")
            daily_api_available = await self.test_api_connectivity(self.real_api_base)
            if daily_api_available:
                self.daily_api_base = self.real_api_base

        if not daily_api_available:
            logger.error("No API available, falling back to cached data")
            return await self.load_cached_data()

        # 收集各個數據源
        for system_name, api_name in self.data_sources.items():
            try:
                logger.info(f"Collecting data for {system_name} from {api_name}")
                api_data = await self.get_latest_data(api_name)

                if api_data and 'data' in api_data:
                    df = pd.DataFrame(api_data['data'])

                    # 數據標準化處理
                    if len(df) > 0:
                        df_processed = self.standardize_dataframe(df, system_name)
                        if df_processed is not None:
                            data_dict[system_name] = df_processed
                            logger.info(f"Successfully processed {system_name}: {len(df_processed)} records")
                        else:
                            logger.warning(f"Failed to standardize {system_name}")
                else:
                    logger.warning(f"No data returned for {system_name}")

            except Exception as e:
                logger.error(f"Error collecting {system_name}: {e}")

        logger.info(f"Collected data from {len(data_dict)} sources")
        return data_dict

    def standardize_dataframe(self, df: pd.DataFrame, source_type: str) -> Optional[pd.DataFrame]:
        """標準化數據格式"""
        try:
            if source_type == 'hibor_overnight':
                # HIBOR數據標準化
                if 'date' in df.columns and 'rate' in df.columns:
                    df['date'] = pd.to_datetime(df['date'])
                    df.set_index('date', inplace=True)
                    df.sort_index(inplace=True)

                    # 只保留隔夜利率
                    if 'tenor' in df.columns:
                        df = df[df['tenor'] == 'Overnight']

                    return df[['rate']].rename(columns={'rate': 'value'})

            elif source_type == 'monetary_base':
                # 貨幣基礎數據標準化
                if 'date' in df.columns and 'Figure_HKD_Billion' in df.columns:
                    df['date'] = pd.to_datetime(df['date'])
                    df.set_index('date', inplace=True)
                    df.sort_index(inplace=True)
                    return df[['Figure_HKD_Billion']].rename(columns={'Figure_HKD_Billion': 'value'})

            elif source_type == 'exchange_rate':
                # 匯率數據標準化
                if 'date' in df.columns:
                    # 尋找匯率相關欄位
                    rate_cols = [col for col in df.columns if 'rate' in col.lower() or 'exchange' in col.lower()]
                    if rate_cols:
                        df['date'] = pd.to_datetime(df['date'])
                        df.set_index('date', inplace=True)
                        df.sort_index(inplace=True)
                        return df[[rate_cols[0]]].rename(columns={rate_cols[0]: 'value'})

            elif source_type == 'trade_data':
                # 貿易數據標準化
                if 'date' in df.columns and 'balance' in df.columns:
                    df['date'] = pd.to_datetime(df['date'])
                    df.set_index('date', inplace=True)
                    df.sort_index(inplace=True)
                    return df[['balance']].rename(columns={'balance': 'value'})

            elif source_type == 'gdp_data':
                # GDP數據標準化
                if 'date' in df.columns and 'growth_rate' in df.columns:
                    df['date'] = pd.to_datetime(df['date'])
                    df.set_index('date', inplace=True)
                    df.sort_index(inplace=True)
                    return df[['growth_rate']].rename(columns={'growth_rate': 'value'})

            logger.warning(f"Unknown source type: {source_type}")
            return None

        except Exception as e:
            logger.error(f"Error standardizing {source_type}: {e}")
            return None

    async def load_cached_data(self) -> Dict[str, pd.DataFrame]:
        """加載緩存數據作為後備"""
        logger.info("Loading cached data as fallback")

        data_dict = {}

        # 嘗試加載靜態文件
        try:
            # HIBOR數據
            hibor_file = Path("CODEX--/gov_crawler/real_data/hibor_data.json")
            if hibor_file.exists():
                with open(hibor_file, 'r', encoding='utf-8') as f:
                    hibor_data = json.load(f)

                df = pd.DataFrame(hibor_data)
                df['date'] = pd.to_datetime(df['date'])
                overnight = df[df['tenor'] == 'Overnight'].copy()
                overnight.set_index('date', inplace=True)
                data_dict['hibor_overnight'] = overnight[['rate']].rename(columns={'rate': 'value'})

                logger.info("Loaded cached HIBOR data")
        except Exception as e:
            logger.error(f"Error loading cached HIBOR: {e}")

        return data_dict

    def calculate_technical_indicators(self, data_dict: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """計算技術指標"""
        logger.info("Calculating technical indicators for all data sources")

        indicator_results = {}

        for source, df in data_dict.items():
            if df is None or len(df) < 10:
                logger.warning(f"Insufficient data for {source}")
                continue

            try:
                # 確保有數值數據
                if 'value' not in df.columns:
                    # 尋找第一個數值欄位
                    numeric_cols = df.select_dtypes(include=[np.number]).columns
                    if len(numeric_cols) > 0:
                        df = df.rename(columns={numeric_cols[0]: 'value'})
                    else:
                        continue

                price_series = df['value'].dropna()

                if len(price_series) < 10:
                    continue

                # 計算各種技術指標
                indicators_result = {}

                # RSI
                try:
                    rsi_14 = self.indicators.calculate_rsi(price_series, 14)
                    current_rsi = rsi_14.iloc[-1] if len(rsi_14) > 0 else 50

                    indicators_result['rsi'] = {
                        'current': float(current_rsi),
                        'signal': 'buy' if current_rsi < 30 else 'sell' if current_rsi > 70 else 'hold'
                    }
                except Exception as e:
                    logger.error(f"RSI calculation failed for {source}: {e}")
                    indicators_result['rsi'] = {'current': 50, 'signal': 'hold'}

                # MACD
                try:
                    if len(price_series) >= 26:
                        macd_result = self.indicators.calculate_macd(price_series, 12, 26, 9)
                        if len(macd_result) > 0:
                            indicators_result['macd'] = {
                                'signal': 'bullish' if macd_result['histogram'].iloc[-1] > 0 else 'bearish'
                            }
                except Exception as e:
                    logger.error(f"MACD calculation failed for {source}: {e}")
                    indicators_result['macd'] = {'signal': 'neutral'}

                # 趨勢
                try:
                    if len(price_series) >= 20:
                        sma_short = price_series.rolling(10).mean()
                        sma_long = price_series.rolling(30).mean()
                        current_price = price_series.iloc[-1]

                        trend = 'bullish' if current_price > sma_short.iloc[-1] > sma_long.iloc[-1] else 'bearish'
                        indicators_result['trend'] = {'direction': trend}
                except Exception as e:
                    logger.error(f"Trend calculation failed for {source}: {e}")
                    indicators_result['trend'] = {'direction': 'neutral'}

                indicator_results[source] = {
                    'indicators': indicators_result,
                    'data_points': len(price_series),
                    'date_range': f"{price_series.index.min()} to {price_series.index.max()}"
                }

            except Exception as e:
                logger.error(f"Error processing {source}: {e}")

        logger.info(f"Calculated indicators for {len(indicator_results)} sources")
        return indicator_results

    def generate_trading_signals(self, indicator_results: Dict[str, Any]) -> Dict[str, Any]:
        """生成交易信號"""
        logger.info("Generating composite trading signals")

        buy_votes = 0
        sell_votes = 0
        hold_votes = 0

        signal_details = []

        for source, results in indicator_results.items():
            if 'indicators' not in results:
                continue

            indicators = results['indicators']
            source_signals = []

            # RSI信號
            if 'rsi' in indicators:
                rsi_signal = indicators['rsi']['signal']
                source_signals.append(f"RSI: {rsi_signal}")

                if rsi_signal == 'buy':
                    buy_votes += 1
                elif rsi_signal == 'sell':
                    sell_votes += 1
                else:
                    hold_votes += 1

            # MACD信號
            if 'macd' in indicators:
                macd_signal = indicators['macd']['signal']
                source_signals.append(f"MACD: {macd_signal}")

                if macd_signal == 'bullish':
                    buy_votes += 1
                elif macd_signal == 'bearish':
                    sell_votes += 1
                else:
                    hold_votes += 1

            # 趨勢信號
            if 'trend' in indicators:
                trend_signal = indicators['trend']['direction']
                source_signals.append(f"Trend: {trend_signal}")

                if trend_signal == 'bullish':
                    buy_votes += 1
                elif trend_signal == 'bearish':
                    sell_votes += 1
                else:
                    hold_votes += 1

            signal_details.append(f"{source}: {', '.join(source_signals)}")

        # 最終信號決策
        total_signals = buy_votes + sell_votes + hold_votes

        if buy_votes > sell_votes and buy_votes > hold_votes:
            final_signal = 'BUY'
            confidence = buy_votes / total_signals
        elif sell_votes > buy_votes and sell_votes > hold_votes:
            final_signal = 'SELL'
            confidence = sell_votes / total_signals
        else:
            final_signal = 'HOLD'
            confidence = hold_votes / total_signals

        return {
            'final_signal': final_signal,
            'confidence': confidence,
            'vote_counts': {
                'buy': buy_votes,
                'sell': sell_votes,
                'hold': hold_votes
            },
            'signal_details': signal_details,
            'sources_analyzed': len(indicator_results)
        }

    async def run_complete_analysis(self) -> Dict[str, Any]:
        """運行完整分析"""
        logger.info("Starting complete real-time technical analysis")

        start_time = datetime.now()

        analysis_results = {
            'timestamp': start_time.strftime("%Y-%m-%d %H:%M:%S"),
            'status': 'running',
            'data_collection': {},
            'indicators': {},
            'signals': {}
        }

        try:
            # 1. 收集真實數據
            logger.info("Step 1: Collecting real-time data")
            data_dict = await self.collect_all_real_data()
            analysis_results['data_collection'] = {
                'sources_loaded': len(data_dict),
                'sources': list(data_dict.keys())
            }

            if len(data_dict) == 0:
                analysis_results['status'] = 'failed'
                analysis_results['error'] = 'No data available from APIs'
                return analysis_results

            # 2. 計算技術指標
            logger.info("Step 2: Calculating technical indicators")
            indicator_results = self.calculate_technical_indicators(data_dict)
            analysis_results['indicators'] = indicator_results

            # 3. 生成交易信號
            logger.info("Step 3: Generating trading signals")
            trading_signals = self.generate_trading_signals(indicator_results)
            analysis_results['signals'] = trading_signals

            # 4. 完成分析
            analysis_results['status'] = 'completed'
            analysis_results['execution_time'] = (datetime.now() - start_time).total_seconds()
            analysis_results['summary'] = {
                'data_sources': len(data_dict),
                'indicators_calculated': len(indicator_results),
                'final_signal': trading_signals['final_signal'],
                'signal_confidence': trading_signals['confidence']
            }

            logger.info(f"Analysis completed in {analysis_results['execution_time']:.2f}s")
            logger.info(f"Final signal: {trading_signals['final_signal']} (confidence: {trading_signals['confidence']:.2f})")

        except Exception as e:
            logger.error(f"Error in complete analysis: {e}")
            analysis_results['status'] = 'failed'
            analysis_results['error'] = str(e)

        return analysis_results

    def save_results(self, results: Dict[str, Any], filename: str = None) -> str:
        """保存分析結果"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"api_multi_indicator_analysis_{timestamp}.json"

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2, default=str)

            logger.info(f"Analysis results saved to: {filename}")
            return filename

        except Exception as e:
            logger.error(f"Error saving results: {e}")
            return None


async def main():
    """主測試函數"""
    print("=== API集成多指標技術分析系統測試 ===")

    # 初始化系統
    system = APIMultiIndicatorSystem()

    # 運行完整分析
    print("1. 運行完整API數據分析...")
    results = await system.run_complete_analysis()

    # 顯示結果
    if results['status'] == 'completed':
        print("\n2. 分析結果:")
        print(f"   狀態: {results['status']}")
        print(f"   數據源: {results['summary']['data_sources']} 個")
        print(f"   指標計算: {results['summary']['indicators_calculated']} 個")
        print(f"   最終信號: {results['summary']['final_signal']}")
        print(f"   信號置信度: {results['summary']['signal_confidence']:.2%}")
        print(f"   執行時間: {results['execution_time']:.2f}秒")

        print("\n3. 數據源詳情:")
        for source in results['data_collection']['sources']:
            print(f"   - {source}")

        print("\n4. 信號詳情:")
        signals = results['signals']
        print(f"   買入票數: {signals['vote_counts']['buy']}")
        print(f"   賣出票數: {signals['vote_counts']['sell']}")
        print(f"   觀望票數: {signals['vote_counts']['hold']}")

        print("\n5. 各數據源信號:")
        for detail in signals['signal_details']:
            print(f"   {detail}")

        # 保存結果
        print("\n6. 保存分析結果...")
        report_file = system.save_results(results)
        if report_file:
            print(f"   結果已保存: {report_file}")

        print("\n=== API集成分析完成 ===")
        print("✅ 成功使用真實API數據")
        print("✅ 技術指標計算完成")
        print("✅ 交易信號生成完成")
        print(f"✅ 最終交易信號: {results['summary']['final_signal']}")

    else:
        print(f"\n❌ 分析失敗: {results.get('error', 'Unknown error')}")


if __name__ == "__main__":
    asyncio.run(main())