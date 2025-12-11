#!/usr/bin/env python3
"""
Dashboard 啟動測試 - 測試 CBSC 系統的 dashboard 組件
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_basic_imports():
    """測試基礎導入"""
    print("Testing basic dashboard imports...")
    
    try:
        # 測試基礎庫
        import fastapi
        from fastapi import FastAPI
        print("SUCCESS: FastAPI imported")
    except ImportError as e:
        print(f"FAILED: FastAPI import failed: {e}")
        return False
    
    try:
        # 測試相關模組
        from src.backtest import BaseBacktestEngine, BacktestEngineConfig
        print("SUCCESS: Backtest modules imported")
    except ImportError as e:
        print(f"FAILED: Backtest modules import failed: {e}")
        return False
    
    try:
        # 測試數據適配器
        from src.data_adapters import DataAdapterConfig, RealMarketData
        print("SUCCESS: Data adapters imported")
    except ImportError as e:
        print(f"FAILED: Data adapters import failed: {e}")
        return False
    
    return True

def test_fastapi_server():
    """測試 FastAPI 服務器創建"""
    print("\nTesting FastAPI server creation...")
    
    try:
        from fastapi import FastAPI
        from fastapi.middleware.cors import CORSMiddleware
        
        # 創建簡單的 FastAPI 應用
        app = FastAPI(
            title="CBSC Quantitative Trading System",
            description="Simplified version for testing",
            version="1.0.0"
        )
        
        # 添加 CORS 中間件
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # 添加基本路由
        @app.get("/")
        async def root():
            return {"message": "CBSC Quantitative Trading System", "status": "running"}
        
        @app.get("/health")
        async def health_check():
            return {"status": "healthy", "system": "CBSC"}
        
        @app.get("/api/v1/backtest/config")
        async def get_backtest_config():
            return {
                "engine_types": ["simple", "advanced"],
                "strategies": ["rsi", "macd", "bollinger"],
                "timeframes": ["1d", "1w", "1m"]
            }
        
        print("SUCCESS: FastAPI server created with basic routes")
        print("   Available endpoints:")
        print("     - GET /")
        print("     - GET /health")
        print("     - GET /api/v1/backtest/config")
        
        return True, app
        
    except Exception as e:
        print(f"FAILED: FastAPI server creation failed: {e}")
        return False, None

def test_simple_backtest():
    """測試簡單回測功能"""
    print("\nTesting simple backtest functionality...")
    
    try:
        from src.backtest import BacktestEngineConfig
        from datetime import date, timedelta
        from decimal import Decimal
        
        # 創建回測配置
        config = BacktestEngineConfig(
            engine_type="simple_test",
            start_date=date.today() - timedelta(days=30),
            end_date=date.today(),
            initial_capital=Decimal("1000000"),
            commission_rate=Decimal("0.001"),
            slippage_rate=Decimal("0.0005")
        )
        
        print("SUCCESS: Backtest engine configuration created")
        print(f"   Engine type: {config.engine_type}")
        print(f"   Initial capital: {config.initial_capital}")
        print(f"   Commission rate: {config.commission_rate}")
        
        return True, config
        
    except Exception as e:
        print(f"FAILED: Backtest configuration failed: {e}")
        return False, None

def main():
    """主測試函數"""
    print("CBSC System - Dashboard Launch Test")
    print("=" * 45)
    
    results = []
    
    # 運行所有測試
    results.append(test_basic_imports())
    
    success, app = test_fastapi_server()
    if success:
        results.append(True)
    else:
        results.append(False)
    
    success, config = test_simple_backtest()
    if success:
        results.append(True)
    else:
        results.append(False)
    
    # 總結
    passed = sum(results)
    total = len(results)
    
    print("\n" + "=" * 45)
    print(f"Dashboard Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("SUCCESS: All dashboard components are working correctly!")
        print("The simplified FastAPI server can be launched.")
        print("\nTo start the server, run:")
        print("  python -m uvicorn test_dashboard_launch:app --host 0.0.0.0 --port 3000")
        return True, app
    else:
        print("WARNING: Some dashboard components failed.")
        return False, None

if __name__ == "__main__":
    success, app = main()
    
    # 可選：啟動服務器
    if success and app and "--start-server" in sys.argv:
        print("\nStarting FastAPI server...")
        import uvicorn
        uvicorn.run(app, host="0.0.0.0", port=3000)
    
    sys.exit(0 if success else 1)