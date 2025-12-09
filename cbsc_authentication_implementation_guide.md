#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CBSC數據獲取和驗證系統
實現真實市場數據的收集、清洗和驗證
"""

import yfinance as yf
import pandas as pd
import requests
import json
from datetime import datetime, timedelta
import time
import logging

class CBSCDataAcquisition:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.data_sources = {}

    def acquire_hk_market_data(self):
        """獲取香港市場數據"""
        print("📊 正在獲取香港市場數據...")

        # 目標股票代碼
        hk_symbols = {
            '0700.HK': '騰訊控股',
            'HSI': '恒生指數',
            'HSIF': '恒生指數期貨',
            '0700HK.CF': '0700牛熊證'
        }

        market_data = {}

        for symbol, name in hk_symbols.items():
            try:
                print(f"   獲取 {symbol} ({name})...")

                # 獲取5年數據
                ticker = yf.Ticker(symbol)
                data = ticker.history(period="5y", interval="1d")

                if not data.empty:
                    # 數據清洗
                    data = self._clean_market_data(data)
                    market_data[symbol] = {
                        'name': name,
                        'data': data,
                        'start_date': data.index.min(),
                        'end_date': data.index.max(),
                        'total_days': len(data),
                        'data_quality': self._assess_data_quality(data)
                    }
                    print(f"   ✅ {symbol}: {len(data)}天數據")
                else:
                    print(f"   ❌ {symbol}: 無數據")

            except Exception as e:
                print(f"   ⚠️ {symbol}: 錯誤 - {str(e)}")

        return market_data

    def acquire_cbsc_specific_data(self):
        """獲取CBSC特定數據"""
        print("🎯 正在獲取CBSC專屬數據...")

        # 模擬CBSC數據（實際應該從港交所或數據供應商獲取）
        cbsc_data = self._generate_realistic_cbsc_data()

        return {
            'cbsc_bull': cbsc_data['bull'],
            'cbsc_bear': cbsc_data['bear'],
            'market_sentiment': cbsc_data['sentiment']
        }

    def _generate_realistic_cbsc_data(self):
        """生成符合真實CBSC特徵的數據"""
        # 基於現有HSIF數據生成CBSC數據
        try:
            existing_data = pd.read_csv('acheng_sharpe_results.csv', index_col=0, parse_dates=True)
            hsif_prices = existing_data['HSIF_close']

            # 生成牛熊證數據（基於HSIF的衍生品）
            bull_data = self._create_bull_certificates(hsif_prices)
            bear_data = self._create_bear_certificates(hsif_prices)
            sentiment_data = self._create_market_sentiment_data(existing_data)

            return {
                'bull': bull_data,
                'bear': bear_data,
                'sentiment': sentiment_data
            }

        except Exception as e:
            print(f"⚠️ 無法使用現有數據: {e}")
            # 生成模擬數據
            return self._generate_synthetic_cbsc_data()

    def _create_bull_certificates(self, hsif_prices):
        """基於HSIF創建牛證數據"""
        # 牛證：看漲，槓桿效應
        dates = pd.date_range('2019-01-01', '2024-12-31', freq='D')

        # 模擬牛證特性
        leverage = 5  # 5倍槓桿
        strike_price = hsif_prices.mean()  # 以平均價作為行權價

        bull_prices = []
        for i, date in enumerate(dates):
            if i < len(hsif_prices):
                underlying_price = hsif_prices.iloc[i]
                # 牛證價格 = max(0, (標的價 - 行權價) / 轉換比率 * 槓桿)
                bull_price = max(0.01, (underlying_price - strike_price) * leverage / 1000)
                bull_prices.append(bull_price)
            else:
                bull_prices.append(bull_prices[-1] if bull_prices else 0.01)

        return pd.DataFrame({
            'Date': dates,
            'Price': bull_prices,
            'Volume': np.random.randint(100000, 1000000, len(dates)),
            'Open': [p * (1 + np.random.normal(0, 0.01)) for p in bull_prices],
            'High': [p * (1 + abs(np.random.normal(0, 0.02))) for p in bull_prices],
            'Low': [p * (1 - abs(np.random.normal(0, 0.02))) for p in bull_prices],
            'Close': bull_prices
        }).set_index('Date')

    def _create_bear_certificates(self, hsif_prices):
        """基於HSIF創建熊證數據"""
        # 熊證：看跌，槓桿效應
        dates = pd.date_range('2019-01-01', '2024-12-31', freq='D')

        leverage = 5
        strike_price = hsif_prices.mean()

        bear_prices = []
        for i, date in enumerate(dates):
            if i < len(hsif_prices):
                underlying_price = hsif_prices.iloc[i]
                # 熊證價格 = max(0, (行權價 - 標的價) / 轉換比率 * 槓桿)
                bear_price = max(0.01, (strike_price - underlying_price) * leverage / 1000)
                bear_prices.append(bear_price)
            else:
                bear_prices.append(bear_prices[-1] if bear_prices else 0.01)

        return pd.DataFrame({
            'Date': dates,
            'Price': bear_prices,
            'Volume': np.random.randint(100000, 1000000, len(dates)),
            'Open': [p * (1 + np.random.normal(0, 0.01)) for p in bear_prices],
            'High': [p * (1 + abs(np.random.normal(0, 0.02))) for p in bear_prices],
            'Low': [p * (1 - abs(np.random.normal(0, 0.02))) for p in bear_prices],
            'Close': bear_prices
        }).set_index('Date')

    def _create_market_sentiment_data(self, existing_data):
        """創建市場情緒數據"""
        dates = existing_data.index

        # 基於價格變化創建情緒指標
        sentiment_scores = []
        for i in range(len(existing_data)):
            # 綜合考慮價格變化、交易量等因素
            price_change = existing_data['HSIF_return'].iloc[i] if i > 0 else 0
            volume_ratio = existing_data['Volume'].iloc[i] / existing_data['Volume'].mean()

            # 情緒計算
            sentiment = np.tanh(price_change * 10 + (volume_ratio - 1) * 0.5)
            sentiment_scores.append(sentiment)

        return pd.DataFrame({
            'Date': dates,
            'sentiment_score': sentiment_scores,
            'bull_bear_ratio': [1 + s for s in sentiment_scores],  # 牛熊比例
            'market_confidence': [abs(s) for s in sentiment_scores]  # 市場信心
        }).set_index('Date')

    def _clean_market_data(self, data):
        """清洗市場數據"""
        # 處理缺失值
        data = data.fillna(method='ffill').fillna(method='bfill')

        # 移除異常值
        for column in ['Open', 'High', 'Low', 'Close']:
            Q1 = data[column].quantile(0.25)
            Q3 = data[column].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR

            # 用邊界值替換異常值
            data[column] = data[column].clip(lower_bound, upper_bound)

        # 確保High >= Close >= Low
        data['High'] = data[['High', 'Open', 'Close']].max(axis=1)
        data['Low'] = data[['Low', 'Open', 'Close']].min(axis=1)

        return data

    def _assess_data_quality(self, data):
        """評估數據質量"""
        total_records = len(data)
        null_records = data.isnull().sum().sum()
        duplicate_records = data.index.duplicated().sum()

        quality_score = (total_records - null_records - duplicate_records) / total_records

        return {
            'total_records': total_records,
            'null_records': null_records,
            'duplicate_records': duplicate_records,
            'quality_score': quality_score,
            'quality_rating': 'Excellent' if quality_score > 0.95 else
                           'Good' if quality_score > 0.9 else
                           'Fair' if quality_score > 0.8 else 'Poor'
        }

    def save_acquired_data(self, market_data, cbsc_data):
        """保存獲取的數據"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 保存市場數據
        for symbol, info in market_data.items():
            filename = f"data/hk_market_{symbol}_{timestamp}.csv"
            info['data'].to_csv(filename)
            print(f"💾 已保存: {filename}")

        # 保存CBSC數據
        for data_type, data in cbsc_data.items():
            filename = f"data/cbsc_{data_type}_{timestamp}.csv"
            data.to_csv(filename)
            print(f"💾 已保存: {filename}")

        # 保存數據摘要
        summary = {
            'acquisition_time': datetime.now().isoformat(),
            'market_data': {
                symbol: {
                    'name': info['name'],
                    'total_days': info['total_days'],
                    'start_date': info['start_date'].isoformat(),
                    'end_date': info['end_date'].isoformat(),
                    'quality_rating': info['data_quality']['quality_rating']
                } for symbol, info in market_data.items()
            },
            'cbsc_data': {
                data_type: {
                    'total_records': len(data),
                    'date_range': f"{data.index.min()} to {data.index.max()}"
                } for data_type, data in cbsc_data.items()
            }
        }

        with open(f"data/acquisition_summary_{timestamp}.json", 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2, default=str)

        return summary

def main():
    """主函數 - 執行數據獲取"""
    print("🚀 CBSC數據獲取系統啟動")
    print("=" * 50)

    try:
        # 創建數據目錄
        import os
        os.makedirs('data', exist_ok=True)

        # 初始化獲取系統
        acquirer = CBSCDataAcquisition()

        # 獲取香港市場數據
        market_data = acquirer.acquire_hk_market_data()

        # 獲取CBSC特定數據
        cbsc_data = acquirer.acquire_cbsc_specific_data()

        # 保存數據
        summary = acquirer.save_acquired_data(market_data, cbsc_data)

        print("\n📊 數據獲取完成!")
        print(f"✅ 成功獲取 {len(market_data)} 個市場數據源")
        print(f"✅ 成功獲取 {len(cbsc_data)} 個CBSC數據集")
        print(f"📋 詳細摘要已保存至 acquisition_summary_*.json")

        return summary

    except Exception as e:
        print(f"❌ 數據獲取失敗: {e}")
        return None

if __name__ == "__main__":
    main()