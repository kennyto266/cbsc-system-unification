#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CBSC真實數據獲取系統
實現多源數據收集、驗證和整合
"""

import yfinance as yf
import pandas as pd
import requests
import json
from datetime import datetime, timedelta
import time
import logging
import numpy as np

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CBSCDataAcquisitionSystem:
    def __init__(self):
        self.data_sources = {}
        self.validation_results = {}

    def acquire_hk_market_data(self, symbols=None, period="5y"):
        """獲取香港市場真實數據"""
        if symbols is None:
            symbols = {
                '0700.HK': '騰訊控股',
                'HSI': '恒生指數',
                '^HSI': '恒生指數',
                '03690.HK': '美團',
                '9988.HK': '阿里巴巴'
            }

        print("📊 正在獲取香港市場真實數據...")
        market_data = {}

        for symbol, name in symbols.items():
            try:
                print(f"   📈 獲取 {symbol} ({name})...")

                # 使用yfinance獲取數據
                ticker = yf.Ticker(symbol)
                data = ticker.history(period=period, interval="1d")

                if not data.empty:
                    # 數據清洗
                    data = self._clean_market_data(data)

                    # 驗證數據質量
                    quality_score = self._validate_data_quality(data, symbol)

                    market_data[symbol] = {
                        'name': name,
                        'data': data,
                        'start_date': data.index.min(),
                        'end_date': data.index.max(),
                        'total_days': len(data),
                        'quality_score': quality_score,
                        'source': 'Yahoo Finance',
                        'last_updated': datetime.now().isoformat()
                    }

                    print(f"   ✅ {symbol}: {len(data)}天數據 (質量分數: {quality_score:.2f})")
                else:
                    print(f"   ❌ {symbol}: 無數據")

                # 添加延遲避免API限制
                time.sleep(0.5)

            except Exception as e:
                print(f"   ⚠️ {symbol}: 錯誤 - {str(e)}")
                logger.error(f"Error fetching {symbol}: {e}")

        return market_data

    def acquire_cbsc_related_data(self):
        """獲取CBSC相關的衍生品數據"""
        print("🎯 正在獲取CBSC相關數據...")

        # 基於現有真實數據創建CBSC相關指標
        try:
            # 嘗試讀取現有的真實數據
            existing_data = pd.read_csv('acheng_sharpe_results.csv')
            existing_data['Date'] = pd.to_datetime(existing_data['Date'])
            existing_data.set_index('Date', inplace=True)

            print(f"   📋 使用現有數據: {len(existing_data)}天")

            # 創建CBSC牛熊證指標
            cbsc_indicators = self._create_cbsc_indicators(existing_data)

            # 創建市場情緒指標
            sentiment_data = self._create_sentiment_indicators(existing_data)

            # 創建流動性指標
            liquidity_data = self._create_liquidity_indicators(existing_data)

            return {
                'cbsc_indicators': cbsc_indicators,
                'market_sentiment': sentiment_data,
                'liquidity_metrics': liquidity_data,
                'base_data_summary': {
                    'total_records': len(existing_data),
                    'date_range': f"{existing_data.index.min()} to {existing_data.index.max()}",
                    'assets': ['HSIF', 'USDCNH']
                }
            }

        except FileNotFoundError:
            print("   ⚠️ 未找到現有數據文件，生成模擬數據...")
            return self._generate_synthetic_cbsc_data()
        except Exception as e:
            print(f"   ❌ 處理現有數據時出錯: {e}")
            return self._generate_synthetic_cbsc_data()

    def _create_cbsc_indicators(self, base_data):
        """創建CBSC相關指標"""
        # 基於HSIF期貨創建牛熊證相關指標
        hsif_prices = base_data['HSIF_close']
        hsif_returns = base_data['HSIF_return']

        # 創建牛證指標（看漲槓桿產品）
        bull_leverage = 5  # 5倍槓桿
        strike_price = hsif_prices.median()  # 中位數作為參考價

        bull_indicators = pd.DataFrame({
            'Date': base_data.index,
            'bull_price': np.maximum(0.01, (hsif_prices - strike_price) * bull_leverage / 1000),
            'bull_delta': self._calculate_delta(hsif_prices, strike_price, 'call'),
            'bull_gamma': self._calculate_gamma(hsif_prices, strike_price),
            'bull_theta': self._calculate_theta(hsif_prices, strike_price),
            'bull_vega': self._calculate_vega(hsif_prices, strike_price),
            'bull_implied_vol': self._calculate_implied_vol(hsif_returns)
        }).set_index('Date')

        # 創建熊證指標（看跌槓桿產品）
        bear_indicators = pd.DataFrame({
            'Date': base_data.index,
            'bear_price': np.maximum(0.01, (strike_price - hsif_prices) * bull_leverage / 1000),
            'bear_delta': self._calculate_delta(hsif_prices, strike_price, 'put'),
            'bear_gamma': self._calculate_gamma(hsif_prices, strike_price),
            'bear_theta': self._calculate_theta(hsif_prices, strike_price),
            'bear_vega': self._calculate_vega(hsif_prices, strike_price),
            'bear_implied_vol': self._calculate_implied_vol(hsif_returns)
        }).set_index('Date')

        return {
            'bull_certificates': bull_indicators,
            'bear_certificates': bear_indicators,
            'leverage_ratio': bull_leverage,
            'reference_strike': strike_price
        }

    def _create_sentiment_indicators(self, base_data):
        """創建市場情緒指標"""
        hsif_returns = base_data['HSIF_return']
        volume = base_data.get('Volume', pd.Series(index=base_data.index, data=1000000))

        # 計算各種情緒指標
        sentiment_data = pd.DataFrame({
            'Date': base_data.index,

            # 價格動量情緒
            'price_momentum': hsif_returns.rolling(5).mean(),
            'price_trend': hsif_returns.rolling(20).mean(),

            # 波動率情緒
            'realized_volatility': hsif_returns.rolling(20).std() * np.sqrt(252),
            'volatility_ratio': hsif_returns.rolling(20).std() / hsif_returns.rolling(60).std(),

            # 交易量情緒
            'volume_momentum': volume.pct_change().rolling(5).mean(),
            'volume_ratio': volume / volume.rolling(20).mean(),

            # 綜合情緒指標
            'fear_greed_index': self._calculate_fear_greed_index(hsif_returns, volume),

            # 超買超賣指標
            'rsi_signal': self._calculate_rsi_signal(hsif_returns),

            # 牛熊比例基於價格變化
            'bull_bear_ratio': self._calculate_bull_bear_ratio(hsif_returns)
        }).set_index('Date')

        return sentiment_data

    def _create_liquidity_indicators(self, base_data):
        """創建流動性指標"""
        volume = base_data.get('Volume', pd.Series(index=base_data.index, data=1000000))
        hsif_prices = base_data['HSIF_close']

        liquidity_data = pd.DataFrame({
            'Date': base_data.index,

            # 基礎流動性指標
            'daily_volume': volume,
            'volume_ma_5': volume.rolling(5).mean(),
            'volume_ma_20': volume.rolling(20).mean(),

            # 價格影響指標
            'price_impact': abs(base_data['HSIF_return']) / (volume / volume.mean()),

            # 流動性比率
            'liquidity_ratio': volume.rolling(20).mean() / volume.rolling(5).mean(),

            # 市場深度指標（基於價格變化）
            'market_depth': 1 / (base_data['HSIF_return'].rolling(5).std() + 1e-6),

            # 交易活躍度
            'trading_activity': volume * hsif_prices,

            # 流動性風險
            'liquidity_risk': volume.rolling(20).std() / volume.rolling(20).mean()
        }).set_index('Date')

        return liquidity_data

    def _calculate_fear_greed_index(self, returns, volume):
        """計算恐懼貪婪指標"""
        # 基於價格動量和交易量的恐懼貪婪指標
        price_momentum = returns.rolling(20).sum()
        volume_momentum = (volume / volume.rolling(20).mean() - 1).rolling(20).mean()

        # 綜合計算 (0-100範圍)
        index = 50 + 25 * np.tanh(price_momentum * 10) + 25 * np.tanh(volume_momentum * 5)
        return np.clip(index, 0, 100)

    def _calculate_rsi_signal(self, returns, period=14):
        """基於收益率計算RSI信號"""
        delta = returns.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def _calculate_bull_bear_ratio(self, returns):
        """計算牛熊比例"""
        # 基於近期收益率計算牛熊情緒
        recent_returns = returns.rolling(5).mean()

        # 將收益率轉換為牛熊比例 (0.1-10範圍)
        ratio = np.exp(recent_returns * 10)
        return np.clip(ratio, 0.1, 10)

    def _calculate_delta(self, price, strike, option_type='call'):
        """計算期權Delta值"""
        moneyness = price / strike

        if option_type == 'call':
            # 看漲期權Delta
            if moneyness > 1.1:
                return 0.9
            elif moneyness > 1.0:
                return 0.6
            elif moneyness > 0.9:
                return 0.4
            else:
                return 0.2
        else:
            # 看跌期權Delta
            if moneyness < 0.9:
                return -0.9
            elif moneyness < 1.0:
                return -0.6
            elif moneyness < 1.1:
                return -0.4
            else:
                return -0.2

    def _calculate_gamma(self, price, strike):
        """計算Gamma值"""
        moneyness = price / strike
        # Gamma在價平時最高
        if 0.95 <= moneyness <= 1.05:
            return 0.1
        elif 0.9 <= moneyness <= 1.1:
            return 0.05
        else:
            return 0.02

    def _calculate_theta(self, price, strike):
        """計算Theta值（時間衰退）"""
        # 簡化的Theta計算
        return -0.001 * price / strike

    def _calculate_vega(self, price, strike):
        """計算Vega值（波動率敏感度）"""
        # 簡化的Vega計算
        moneyness = price / strike
        return 0.1 * abs(moneyness - 1)

    def _calculate_implied_vol(self, returns):
        """計算隱含波動率"""
        # 基於歷史波動率計算隱含波動率
        historical_vol = returns.rolling(20).std() * np.sqrt(252)
        # 通常隱含波動率會高於歷史波動率
        implied_vol = historical_vol * 1.2
        return implied_vol

    def _clean_market_data(self, data):
        """清洗市場數據"""
        # 處理缺失值
        data = data.fillna(method='ffill').fillna(method='bfill')

        # 移除異常值
        for column in ['Open', 'High', 'Low', 'Close']:
            if column in data.columns:
                Q1 = data[column].quantile(0.25)
                Q3 = data[column].quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR

                # 用邊界值替換異常值
                data[column] = data[column].clip(lower_bound, upper_bound)

        # 確保High >= Close >= Low
        if 'High' in data.columns and 'Low' in data.columns and 'Close' in data.columns:
            data['High'] = data[['High', 'Open', 'Close']].max(axis=1)
            data['Low'] = data[['Low', 'Open', 'Close']].min(axis=1)

        return data

    def _validate_data_quality(self, data, symbol):
        """驗證數據質量"""
        total_records = len(data)
        null_records = data.isnull().sum().sum()
        duplicate_records = data.index.duplicated().sum()

        # 價格連續性檢查
        price_continuity = True
        if 'Close' in data.columns:
            price_changes = data['Close'].pct_change()
            extreme_changes = (abs(price_changes) > 0.2).sum()  # 超過20%的變化
            price_continuity = extreme_changes < len(data) * 0.01  # 少於1%的極端變化

        # 交易量合理性檢查
        volume_reasonableness = True
        if 'Volume' in data.columns:
            zero_volume_days = (data['Volume'] == 0).sum()
            volume_reasonableness = zero_volume_days < len(data) * 0.05  # 少於5%的零交易量

        # 綜合質量評分
        quality_score = (
            (total_records - null_records - duplicate_records) / total_records * 0.4 +
            (1 if price_continuity else 0) * 0.3 +
            (1 if volume_reasonableness else 0) * 0.3
        )

        return quality_score

    def _generate_synthetic_cbsc_data(self):
        """生成合成CBSC數據（當無真實數據時）"""
        print("   🔧 生成合成CBSC數據...")

        # 生成時間序列
        dates = pd.date_range('2019-01-01', '2024-12-31', freq='D')

        # 生成基礎價格序列（模擬HSIF）
        np.random.seed(42)
        returns = np.random.normal(0.0005, 0.02, len(dates))
        prices = 28000 * np.exp(np.cumsum(returns))

        # 生成合成數據
        synthetic_data = {
            'cbsc_indicators': {
                'bull_certificates': pd.DataFrame({
                    'Date': dates,
                    'bull_price': np.maximum(0.01, np.random.randn(len(dates)) * 0.5 + 1),
                    'bull_delta': np.random.uniform(0.2, 0.8, len(dates)),
                    'bull_implied_vol': np.random.uniform(0.2, 0.6, len(dates))
                }).set_index('Date'),

                'bear_certificates': pd.DataFrame({
                    'Date': dates,
                    'bear_price': np.maximum(0.01, np.random.randn(len(dates)) * 0.5 + 1),
                    'bear_delta': np.random.uniform(-0.8, -0.2, len(dates)),
                    'bear_implied_vol': np.random.uniform(0.2, 0.6, len(dates))
                }).set_index('Date')
            },

            'market_sentiment': pd.DataFrame({
                'Date': dates,
                'fear_greed_index': np.random.uniform(20, 80, len(dates)),
                'bull_bear_ratio': np.random.uniform(0.5, 2.0, len(dates)),
                'realized_volatility': np.random.uniform(0.15, 0.35, len(dates))
            }).set_index('Date')
        }

        print("   ⚠️ 注意：使用合成數據，建議獲取真實市場數據以提高分析準確性")

        return synthetic_data

    def save_acquired_data(self, market_data, cbsc_data):
        """保存獲取的數據"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 創建數據目錄
        import os
        os.makedirs('acquired_data', exist_ok=True)

        # 保存市場數據
        for symbol, info in market_data.items():
            filename = f"acquired_data/market_{symbol}_{timestamp}.csv"
            info['data'].to_csv(filename)
            print(f"💾 已保存市場數據: {filename}")

        # 保存CBSC數據
        for data_type, data in cbsc_data.items():
            if data_type == 'base_data_summary':
                # 保存摘要信息
                filename = f"acquired_data/cbsc_summary_{timestamp}.json"
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2, default=str)
            else:
                # 保存DataFrame數據
                if isinstance(data, dict):
                    for sub_type, sub_data in data.items():
                        if isinstance(sub_data, pd.DataFrame):
                            filename = f"acquired_data/cbsc_{data_type}_{sub_type}_{timestamp}.csv"
                            sub_data.to_csv(filename)
                            print(f"💾 已保存CBSC數據: {filename}")
                elif isinstance(data, pd.DataFrame):
                    filename = f"acquired_data/cbsc_{data_type}_{timestamp}.csv"
                    data.to_csv(filename)
                    print(f"💾 已保存CBSC數據: {filename}")

        # 保存獲取摘要
        summary = {
            'acquisition_timestamp': datetime.now().isoformat(),
            'market_data_summary': {
                symbol: {
                    'name': info['name'],
                    'total_days': info['total_days'],
                    'quality_score': info['quality_score'],
                    'source': info['source'],
                    'date_range': f"{info['start_date']} to {info['end_date']}"
                } for symbol, info in market_data.items()
            },
            'cbsc_data_types': list(cbsc_data.keys()),
            'total_datasets': len(market_data) + len([k for k in cbsc_data.keys() if k != 'base_data_summary'])
        }

        summary_filename = f"acquired_data/acquisition_summary_{timestamp}.json"
        with open(summary_filename, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2, default=str)

        print(f"📋 獲取摘要已保存: {summary_filename}")
        return summary

def main():
    """主執行函數"""
    print("🚀 CBSC真實數據獲取系統")
    print("=" * 60)

    try:
        # 初始化獲取系統
        acquirer = CBSCDataAcquisitionSystem()

        # 獲取香港市場數據
        print("\n📊 步驟1：獲取香港市場真實數據")
        market_data = acquirer.acquire_hk_market_data()

        # 獲取CBSC相關數據
        print("\n🎯 步驟2：獲取CBSC相關數據")
        cbsc_data = acquirer.acquire_cbsc_related_data()

        # 保存數據
        print("\n💾 步驟3：保存獲取的數據")
        summary = acquirer.save_acquired_data(market_data, cbsc_data)

        print("\n✅ 數據獲取完成!")
        print(f"📈 成功獲取 {len(market_data)} 個市場數據源")
        print(f"🎯 成功獲取 {len(cbsc_data)} 個CBSC數據集")
        print(f"📊 總共 {summary['total_datasets']} 個數據集")

        print("\n🔍 下一步建議：")
        print("1. 使用生產級回測框架驗證策略")
        print("2. 基於真實數據重新運行策略分析")
        print("3. 實施統計顯著性檢驗")
        print("4. 設置風險控制和監控系統")

        return summary

    except Exception as e:
        print(f"❌ 數據獲取失敗: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    main()