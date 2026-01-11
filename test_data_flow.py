#!/usr/bin/env python3
"""
數據流驗證 - 測試 CBSC 系統的數據處理和轉換能力
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def test_market_data_pipeline():
    """測試市場數據處理管道"""
    print("Testing market data pipeline...")
    
    try:
        import yfinance as yf
        
        # 獲取香港市場數據
        hk_stocks = ['0700.HK', '1398.HK', '0941.HK']
        data_dict = {}
        
        for symbol in hk_stocks:
            try:
                stock = yf.Ticker(symbol)
                data = stock.history(period="1mo")
                if not data.empty:
                    data_dict[symbol] = data
                    print(f"SUCCESS: Retrieved {len(data)} days of {symbol} data")
                else:
                    print(f"WARNING: No data for {symbol}")
            except Exception as e:
                print(f"FAILED: Error retrieving {symbol}: {e}")
                continue
        
        if data_dict:
            print(f"SUCCESS: Pipeline processed {len(data_dict)} stocks")
            return True, data_dict
        else:
            print("FAILED: No data processed")
            return False, {}
            
    except Exception as e:
        print(f"FAILED: Market data pipeline failed: {e}")
        return False, {}

def test_technical_indicators():
    """測試技術指標計算"""
    print("\nTesting technical indicators...")
    
    try:
        import yfinance as yf
        
        # 獲取測試數據
        stock = yf.Ticker('0700.HK')
        data = stock.history(period="3mo")
        
        if data.empty:
            print("FAILED: No test data available")
            return False
        
        # 計算常用技術指標
        df = data.copy()
        
        # RSI
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # MACD
        exp1 = df['Close'].ewm(span=12).mean()
        exp2 = df['Close'].ewm(span=26).mean()
        df['MACD'] = exp1 - exp2
        df['Signal'] = df['MACD'].ewm(span=9).mean()
        
        # Bollinger Bands
        df['BB_Middle'] = df['Close'].rolling(window=20).mean()
        bb_std = df['Close'].rolling(window=20).std()
        df['BB_Upper'] = df['BB_Middle'] + (bb_std * 2)
        df['BB_Lower'] = df['BB_Middle'] - (bb_std * 2)
        
        # 移動平均
        df['MA_5'] = df['Close'].rolling(window=5).mean()
        df['MA_20'] = df['Close'].rolling(window=20).mean()
        
        print(f"SUCCESS: Calculated {len(df.columns)} indicators")
        print(f"   Latest RSI: {df['RSI'].iloc[-1]:.2f}")
        print(f"   Latest MACD: {df['MACD'].iloc[-1]:.4f}")
        print(f"   Latest Close: {df['Close'].iloc[-1]:.2f}")
        
        return True, df
        
    except Exception as e:
        print(f"FAILED: Technical indicators calculation failed: {e}")
        return False, None

def test_strategy_signals():
    """測試策略信號生成"""
    print("\nTesting strategy signals...")
    
    try:
        # 使用前面的技術指標數據
        success, df = test_technical_indicators()
        if not success or df is None:
            print("FAILED: Cannot generate signals without indicator data")
            return False
        
        # 生成簡單的交易信號
        df = df.dropna()
        
        # RSI 信號
        df['RSI_Signal'] = 0
        df.loc[df['RSI'] < 30, 'RSI_Signal'] = 1  # 超賣信號
        df.loc[df['RSI'] > 70, 'RSI_Signal'] = -1  # 超買信號
        
        # MACD 信號
        df['MACD_Signal'] = 0
        df.loc[df['MACD'] > df['Signal'], 'MACD_Signal'] = 1  # 金叉
        df.loc[df['MACD'] < df['Signal'], 'MACD_Signal'] = -1  # 死叉
        
        # 移動平均信號
        df['MA_Signal'] = 0
        df.loc[df['MA_5'] > df['MA_20'], 'MA_Signal'] = 1  # 短期在長期之上
        df.loc[df['MA_5'] < df['MA_20'], 'MA_Signal'] = -1  # 短期在長期之下
        
        # 綜合信號
        df['Combined_Signal'] = df['RSI_Signal'] + df['MACD_Signal'] + df['MA_Signal']
        
        # 統計信號
        rsi_signals = (df['RSI_Signal'] != 0).sum()
        macd_signals = (df['MACD_Signal'] != 0).sum()
        ma_signals = (df['MA_Signal'] != 0).sum()
        
        print(f"SUCCESS: Generated trading signals")
        print(f"   RSI signals: {rsi_signals}")
        print(f"   MACD signals: {macd_signals}")
        print(f"   MA signals: {ma_signals}")
        print(f"   Latest combined signal: {df['Combined_Signal'].iloc[-1]}")
        
        return True, df
        
    except Exception as e:
        print(f"FAILED: Strategy signal generation failed: {e}")
        return False, None

def test_data_export():
    """測試數據導出功能"""
    print("\nTesting data export...")
    
    try:
        # 獲取數據並導出
        success, df = test_strategy_signals()
        if not success or df is None:
            print("FAILED: Cannot export data without signal data")
            return False
        
        # 導出到 CSV
        csv_file = "test_data_export.csv"
        df.to_csv(csv_file)
        
        if os.path.exists(csv_file):
            file_size = os.path.getsize(csv_file)
            print(f"SUCCESS: Exported data to {csv_file} ({file_size} bytes)")
            
            # 驗證導出數據
            exported_df = pd.read_csv(csv_file, index_col=0, parse_dates=True)
            if len(exported_df) == len(df):
                print(f"SUCCESS: Export verification passed - {len(exported_df)} rows")
                
                # 清理測試文件
                os.remove(csv_file)
                return True
            else:
                print(f"FAILED: Export verification failed - row count mismatch")
                return False
        else:
            print("FAILED: Export file not created")
            return False
            
    except Exception as e:
        print(f"FAILED: Data export failed: {e}")
        return False

def main():
    """主測試函數"""
    print("CBSC System - Data Flow Validation")
    print("=" * 40)
    
    results = []
    
    # 運行數據流測試
    success, _ = test_market_data_pipeline()
    results.append(success)
    
    success, _ = test_technical_indicators()
    results.append(success)
    
    success, _ = test_strategy_signals()
    results.append(success)
    
    success = test_data_export()
    results.append(success)
    
    # 總結
    passed = sum(results)
    total = len(results)
    
    print("\n" + "=" * 40)
    print(f"Data Flow Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("SUCCESS: All data flow tests passed! System data processing is working correctly.")
        return True
    else:
        print("WARNING: Some data flow tests failed.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)