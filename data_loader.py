"""
Data Loader for CBSC Backtesting System
CBSC回測系統數據加載器

Load and align CBSC sentiment data with price data for VectorBT backtesting.
加載和對齊CBSC情緒數據與價格數據以進行VectorBT回測。

Author: CBSC Backtesting System Team
Date: 2025-12-04
"""

import pandas as pd
import numpy as np
import yfinance as yf
from pathlib import Path
from typing import Dict, Tuple, Optional, List
from datetime import datetime, date
import warnings

warnings.filterwarnings('ignore')

class CBSCDataLoader:
    """CBSC數據加載器 - 專為VectorBT回測設計"""

    def __init__(self, sentiment_csv_path: str):
        """
        初始化數據加載器

        Args:
            sentiment_csv_path: CBSC情緒數據CSV文件路徑
        """
        self.sentiment_path = Path(sentiment_csv_path)
        self.sentiment_data = None
        self.price_data = None

    def load_sentiment_data(self) -> pd.DataFrame:
        """
        加載CBSC情緒數據

        Returns:
            處理後的情緒數據DataFrame
        """
        try:
            # 讀取CSV數據
            df = pd.read_csv(self.sentiment_path)

            # 數據清理和預處理
            df['Date'] = pd.to_datetime(df['Date'])

            # 過濾無效數據
            df = df.dropna(subset=['Date', 'Afternoon_Close', 'Bull_Ratio', 'Bull_Bear_Ratio'])

            # 計算關鍵指標
            df['Total_Turnover'] = df['Bull_Turnover_HKD'] + df['Bear_Turnover_HKD']
            df['Sentiment_Strength'] = (df['Bull_Turnover_HKD'] - df['Bear_Turnover_HKD']) / df['Total_Turnover']
            df['Sentiment_Score'] = (df['Sentiment_Strength'] + 1) * 50  # 0-100分數

            # 分組處理重複日期（保留有效數據）
            df = df.loc[df.groupby('Date')['Total_Turnover'].idxmax()]

            # 按日期排序
            df = df.sort_values('Date').reset_index(drop=True)

            # 選擇核心欄位
            core_columns = [
                'Date', 'Afternoon_Close', 'Bull_Ratio', 'Bull_Bear_Ratio',
                'Bull_Turnover_HKD', 'Bear_Turnover_HKD', 'Total_Turnover',
                'Sentiment_Strength', 'Sentiment_Score', 'Signal', 'Sentiment_Level'
            ]

            self.sentiment_data = df[core_columns].copy()
            print(f"成功加載 {len(self.sentiment_data)} 條CBSC情緒數據")

            return self.sentiment_data

        except Exception as e:
            print(f"加載情緒數據失敗: {e}")
            return pd.DataFrame()

    def load_price_data(self, symbol: str = "0700.HK",
                       start_date: Optional[str] = None,
                       end_date: Optional[str] = None) -> pd.DataFrame:
        """
        加載股價數據

        Args:
            symbol: 股票代碼
            start_date: 開始日期
            end_date: 結束日期

        Returns:
            股價數據DataFrame
        """
        try:
            # 如果有情緒數據，使用其日期範圍
            if self.sentiment_data is not None and (start_date is None or end_date is None):
                start_date = self.sentiment_data['Date'].min().strftime('%Y-%m-%d')
                end_date = self.sentiment_data['Date'].max().strftime('%Y-%m-%d')

            # 下載股價數據
            ticker = yf.Ticker(symbol)
            price_df = ticker.history(start=start_date, end=end_date)

            if price_df.empty:
                print(f"警告: 無法獲取 {symbol} 的股價數據")
                return pd.DataFrame()

            # 數據處理
            price_df = price_df.reset_index()
            price_df['Date'] = pd.to_datetime(price_df['Date'])

            # 重命名欄位以保持一致性
            price_df = price_df.rename(columns={
                'Open': 'open',
                'High': 'high',
                'Low': 'low',
                'Close': 'close',
                'Volume': 'volume'
            })

            # 選擇核心欄位
            price_columns = ['Date', 'open', 'high', 'low', 'close', 'volume']
            self.price_data = price_df[price_columns].copy()

            print(f"成功加載 {len(self.price_data)} 條 {symbol} 股價數據")
            return self.price_data

        except Exception as e:
            print(f"加載股價數據失敗: {e}")
            return pd.DataFrame()

    def align_data(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        對齊情緒數據和價格數據

        Returns:
            (對齊後的情緒數據, 對齊後的價格數據)
        """
        if self.sentiment_data is None or self.price_data is None:
            raise ValueError("必須先加載情緒數據和價格數據")

        # 找到共同的日期範圍
        sentiment_dates = set(self.sentiment_data['Date'].dt.date)
        price_dates = set(self.price_data['Date'].dt.date)

        common_dates = sorted(list(sentiment_dates.intersection(price_dates)))

        if not common_dates:
            raise ValueError("情緒數據和價格數據沒有共同的日期")

        # 過濾數據到共同日期範圍
        start_date, end_date = common_dates[0], common_dates[-1]

        aligned_sentiment = self.sentiment_data[
            (self.sentiment_data['Date'].dt.date >= start_date) &
            (self.sentiment_data['Date'].dt.date <= end_date)
        ].copy()

        aligned_price = self.price_data[
            (self.price_data['Date'].dt.date >= start_date) &
            (self.price_data['Date'].dt.date <= end_date)
        ].copy()

        print(f"數據對齊完成: {len(aligned_sentiment)} 條情緒數據, {len(aligned_price)} 條價格數據")
        print(f"日期範圍: {start_date} 至 {end_date}")

        return aligned_sentiment, aligned_price

    def create_cbsc_features(self, sentiment_df: pd.DataFrame,
                           price_df: pd.DataFrame) -> pd.DataFrame:
        """
        創建CBSC特徵數據集

        Args:
            sentiment_df: 情緒數據
            price_df: 價格數據

        Returns:
            合併後的特徵數據
        """
        # 創建日期索引
        sentiment_df['Date_key'] = sentiment_df['Date'].dt.date
        price_df['Date_key'] = price_df['Date'].dt.date

        # 合併數據
        merged_df = pd.merge(
            sentiment_df,
            price_df,
            on='Date_key',
            how='inner',
            suffixes=('_sentiment', '_price')
        )

        # 計算技術指標
        merged_df['Returns'] = merged_df['close'].pct_change()
        merged_df['MA5'] = merged_df['close'].rolling(5).mean()
        merged_df['MA20'] = merged_df['close'].rolling(20).mean()
        merged_df['RSI'] = self._calculate_rsi(merged_df['close'])

        # CBSC特有特徵
        merged_df['Price_to_Sentiment'] = merged_df['close'] / merged_df['Afternoon_Close']
        merged_df['Volume_Sentiment_Ratio'] = merged_df['volume'] / merged_df['Total_Turnover']
        merged_df['Sentiment_Momentum'] = merged_df['Sentiment_Strength'].rolling(3).mean()

        # 信號強度計算
        merged_df['Signal_Strength'] = np.where(
            merged_df['Sentiment_Level'].isin(['EXTREME BULL', 'EXTREME BEAR']),
            merged_df['Sentiment_Strength'] * 1.5,  # 極端情緒加權
            merged_df['Sentiment_Strength']
        )

        # 清理數據
        merged_df = merged_df.dropna().reset_index(drop=True)

        print(f"創建CBSC特徵完成: {len(merged_df)} 條記錄, {len(merged_df.columns)} 個特徵")

        return merged_df

    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """計算RSI指標"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))

        return rsi

    def get_data_summary(self) -> Dict:
        """獲取數據摘要信息"""
        if self.sentiment_data is None or self.price_data is None:
            return {"error": "數據未加載"}

        return {
            "sentiment_records": len(self.sentiment_data),
            "price_records": len(self.price_data),
            "sentiment_date_range": {
                "start": self.sentiment_data['Date'].min().strftime('%Y-%m-%d'),
                "end": self.sentiment_data['Date'].max().strftime('%Y-%m-%d')
            },
            "price_date_range": {
                "start": self.price_data['Date'].min().strftime('%Y-%m-%d'),
                "end": self.price_data['Date'].max().strftime('%Y-%m-%d')
            },
            "avg_sentiment_strength": float(self.sentiment_data['Sentiment_Strength'].mean()),
            "sentiment_volatility": float(self.sentiment_data['Sentiment_Strength'].std()),
            "data_quality": {
                "null_sentiment": int(self.sentiment_data.isnull().sum().sum()),
                "null_price": int(self.price_data.isnull().sum().sum())
            }
        }

def main():
    """測試數據加載器"""
    print("=== CBSC Data Loader 測試 ===")

    # 初始化加載器
    sentiment_path = "CODEX--/warrant_sentiment_daily.csv"
    loader = CBSCDataLoader(sentiment_path)

    # 加載情緒數據
    print("\n1. 加載情緒數據...")
    sentiment_df = loader.load_sentiment_data()
    if sentiment_df.empty:
        print("情緒數據加載失敗")
        return

    # 加載價格數據
    print("\n2. 加載價格數據...")
    price_df = loader.load_price_data("0700.HK")
    if price_df.empty:
        print("價格數據加載失敗")
        return

    # 對齊數據
    print("\n3. 對齊數據...")
    aligned_sentiment, aligned_price = loader.align_data()

    # 創建特徵
    print("\n4. 創建CBSC特徵...")
    features_df = loader.create_cbsc_features(aligned_sentiment, aligned_price)

    # 顯示摘要
    print("\n5. 數據摘要...")
    summary = loader.get_data_summary()
    for key, value in summary.items():
        print(f"  {key}: {value}")

    # 顯示樣本數據
    print("\n6. 樣本數據...")
    print("特徵數據樣本:")
    print(features_df[['Date', 'close', 'Sentiment_Strength', 'Signal', 'RSI']].head())

    print("\n✅ CBSC Data Loader 測試完成！")

if __name__ == "__main__":
    main()