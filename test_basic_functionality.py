#!/usr/bin/env python3
"""
基本功能測試 - 測試 CBSC 系統的核心組件
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_core_imports():
    """測試核心庫導入"""
    print("🧪 測試核心庫導入...")
    
    try:
        import pandas as pd
        import numpy as np
        print("✅ pandas 和 numpy 導入成功")
    except ImportError as e:
        print(f"❌ pandas/numpy 導入失敗: {e}")
        return False
    
    try:
        import yfinance as yf
        print("✅ yfinance 導入成功")
    except ImportError as e:
        print(f"❌ yfinance 導入失敗: {e}")
        return False
    
    try:
        import matplotlib.pyplot as plt
        import plotly.graph_objects as go
        print("✅ 可視化庫導入成功")
    except ImportError as e:
        print(f"❌ 可視化庫導入失敗: {e}")
        return False
    
    try:
        import sklearn
        print("✅ scikit-learn 導入成功")
    except ImportError as e:
        print(f"❌ scikit-learn 導入失敗: {e}")
        return False
    
    return True

def test_basic_data_retrieval():
    """測試基本數據獲取"""
    print("\n🧪 測試基本數據獲取...")
    
    try:
        import yfinance as yf
        import pandas as pd
        
        # 獲取一些基本股票數據
        stock = yf.Ticker("AAPL")
        data = stock.history(period="5d")
        
        if not data.empty:
            print(f"✅ 成功獲取 {len(data)} 天的 AAPL 數據")
            print(f"   數據列: {list(data.columns)}")
            print(f"   最新價格: {data['Close'].iloc[-1]:.2f}")
            return True
        else:
            print("❌ 獲取的數據為空")
            return False
            
    except Exception as e:
        print(f"❌ 數據獲取失敗: {e}")
        return False

def test_basic_technical_analysis():
    """測試基本技術分析"""
    print("\n🧪 測試基本技術分析...")
    
    try:
        import pandas as pd
        import numpy as np
        
        # 創建一些模擬數據
        prices = pd.Series([100, 102, 98, 105, 103, 107, 106, 109, 108, 112])
        
        # 計算簡單移動平均
        sma_5 = prices.rolling(window=5).mean()
        print(f"✅ 成功計算 5日移動平均: {sma_5.iloc[-1]:.2f}")
        
        # 計算簡單 RSI
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=9).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=9).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        print(f"✅ 成功計算 RSI: {rsi.iloc[-1]:.2f}")
        
        return True
        
    except Exception as e:
        print(f"❌ 技術分析計算失敗: {e}")
        return False

def test_ml_capabilities():
    """測試機器學習能力"""
    print("\n🧪 測試機器學習能力...")
    
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
        print(f"✅ 線性回歸訓練成功，預測結果: {prediction[0]:.2f}")
        
        return True
        
    except Exception as e:
        print(f"❌ 機器學習測試失敗: {e}")
        return False

def main():
    """主測試函數"""
    print("🚀 CBSC 量化交易系統 - 基本功能測試")
    print("=" * 50)
    
    results = []
    
    # 運行所有測試
    results.append(test_core_imports())
    results.append(test_basic_data_retrieval())
    results.append(test_basic_technical_analysis())
    results.append(test_ml_capabilities())
    
    # 總結
    passed = sum(results)
    total = len(results)
    
    print("\n" + "=" * 50)
    print(f"📊 測試結果: {passed}/{total} 通過")
    
    if passed == total:
        print("🎉 所有基本功能測試通過！系統基礎設施正常工作。")
        return True
    else:
        print("⚠️  部分測試失敗，需要進一步檢查和修復。")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)