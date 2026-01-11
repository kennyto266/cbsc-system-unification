#!/usr/bin/env python3
"""
基本功能測試 - 測試 CBSC 系統的核心組件
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_core_imports():
    """測試核心庫導入"""
    print("Testing core library imports...")
    
    try:
        import pandas as pd
        import numpy as np
        print("SUCCESS: pandas and numpy imported")
    except ImportError as e:
        print(f"FAILED: pandas/numpy import failed: {e}")
        return False
    
    try:
        import yfinance as yf
        print("SUCCESS: yfinance imported")
    except ImportError as e:
        print(f"FAILED: yfinance import failed: {e}")
        return False
    
    try:
        import matplotlib.pyplot as plt
        import plotly.graph_objects as go
        print("SUCCESS: visualization libraries imported")
    except ImportError as e:
        print(f"FAILED: visualization libraries import failed: {e}")
        return False
    
    try:
        import sklearn
        print("SUCCESS: scikit-learn imported")
    except ImportError as e:
        print(f"FAILED: scikit-learn import failed: {e}")
        return False
    
    return True

def test_basic_data_retrieval():
    """測試基本數據獲取"""
    print("\nTesting basic data retrieval...")
    
    try:
        import yfinance as yf
        import pandas as pd
        
        # 獲取一些基本股票數據
        stock = yf.Ticker("AAPL")
        data = stock.history(period="5d")
        
        if not data.empty:
            print(f"SUCCESS: Retrieved {len(data)} days of AAPL data")
            print(f"   Data columns: {list(data.columns)}")
            print(f"   Latest price: {data['Close'].iloc[-1]:.2f}")
            return True
        else:
            print("FAILED: Retrieved data is empty")
            return False
            
    except Exception as e:
        print(f"FAILED: Data retrieval failed: {e}")
        return False

def test_basic_technical_analysis():
    """測試基本技術分析"""
    print("\nTesting basic technical analysis...")
    
    try:
        import pandas as pd
        import numpy as np
        
        # 創建一些模擬數據
        prices = pd.Series([100, 102, 98, 105, 103, 107, 106, 109, 108, 112])
        
        # 計算簡單移動平均
        sma_5 = prices.rolling(window=5).mean()
        print(f"SUCCESS: Calculated 5-day SMA: {sma_5.iloc[-1]:.2f}")
        
        # 計算簡單 RSI
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=9).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=9).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        print(f"SUCCESS: Calculated RSI: {rsi.iloc[-1]:.2f}")
        
        return True
        
    except Exception as e:
        print(f"FAILED: Technical analysis failed: {e}")
        return False

def test_ml_capabilities():
    """測試機器學習能力"""
    print("\nTesting machine learning capabilities...")
    
    try:
        from sklearn.linear_model import LinearRegression
        import numpy as np
        
        # 創建簡單的線性回歸測試
        X = np.array([[1], [2], [3], [4], [5]]).reshape(-1, 1)
        y = np.array([2, 4, 6, 8, 10])
        
        model = LinearRegression()
        model.fit(X, y)
        
        # 預測
        prediction = model.predict([[6]])
        print(f"SUCCESS: Linear regression trained, prediction: {prediction[0]:.2f}")
        
        return True
        
    except Exception as e:
        print(f"FAILED: ML test failed: {e}")
        return False

def main():
    """主測試函數"""
    print("CBSC Quantitative Trading System - Basic Functionality Test")
    print("=" * 60)
    
    results = []
    
    # 運行所有測試
    results.append(test_core_imports())
    results.append(test_basic_data_retrieval())
    results.append(test_basic_technical_analysis())
    results.append(test_ml_capabilities())
    
    # 總結
    passed = sum(results)
    total = len(results)
    
    print("\n" + "=" * 60)
    print(f"Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("SUCCESS: All basic functionality tests passed! System infrastructure is working.")
        return True
    else:
        print("WARNING: Some tests failed, need further investigation and fixes.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)