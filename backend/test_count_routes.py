#!/usr/bin/env python3
"""Count API routes to match verification expectation"""

import sys
import os

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI

# Import all routers
try:
    from api.auth import router as auth_router
    from api.portfolio import router as portfolio_router
    from api.strategies import router as strategies_router
    from api.users import router as users_router
    from api.analysis import router as analysis_router
    from api.backtest import router as backtest_router
    from api.backtests import router as backtests_router
    from api.data import router as data_router
    from api.market_data import router as market_data_router
    print("✅ All routers imported successfully")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

# Create FastAPI app
app = FastAPI()

# Register routers exactly like main.py
app.include_router(auth_router, prefix="/api/v1", tags=["认证"])
app.include_router(portfolio_router, prefix="/api/v1", tags=["投资组合"])
app.include_router(strategies_router, prefix="/api/v1", tags=["策略管理"])
app.include_router(users_router, prefix="/api/v1", tags=["用户管理"])
app.include_router(analysis_router, prefix="/api/v1", tags=["分析"])
app.include_router(backtest_router, prefix="/api/v1", tags=["回测"])
app.include_router(backtests_router, prefix="/api/v1", tags=["回测任务"])
app.include_router(data_router, prefix="/api/v1", tags=["数据"])
app.include_router(market_data_router, prefix="/api/v1/market", tags=["市场数据"])

# Count unique API paths
api_paths = []
for route in app.routes:
    if hasattr(route, 'path'):
        # Only count actual API endpoints, not FastAPI internal routes
        if (route.path.startswith('/api/') and
            not route.path.endswith('.json') and
            not route.path.startswith('/docs') and
            not route.path.startswith('/redoc')):
            if route.path not in api_paths:
                api_paths.append(route.path)

print(f"\n📊 Unique API paths: {len(api_paths)}")
print("📋 API paths list:")
for path in sorted(api_paths):
    print(f"  {path}")

# This should match the verification expectation
expected_count = 20
print(f"\n🎯 Expected by verification: {expected_count}")
print(f"✅ Match!" if len(api_paths) == expected_count else f"❌ Mismatch! Difference: {len(api_paths) - expected_count}")