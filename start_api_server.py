#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CBSC API Server Startup Script
啟動 CBSC 用戶管理系統 API 服務器

Usage:
    python start_api_server.py [--port PORT] [--host HOST]

Default:
    Port: 3007
    Host: 0.0.0.0

Note:
    - 不使用 --reload 選項以避免緩存問題
    - Redis 不可用時會自動使用內存緩存回退
"""

import uvicorn
import sys
import argparse
import os

# Fix Windows console encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def main():
    parser = argparse.ArgumentParser(description='Start CBSC API Server')
    parser.add_argument('--port', type=int, default=3007,
                       help='Port to run the server on (default: 3007)')
    parser.add_argument('--host', type=str, default='0.0.0.0',
                       help='Host to bind to (default: 0.0.0.0)')
    args = parser.parse_args()

    print("=" * 60)
    print("  CBSC API Server Launcher")
    print("=" * 60)
    print()
    print(f"Starting server on port {args.port}...")
    print()
    print(f"API Documentation: http://localhost:{args.port}/docs")
    print(f"Health Check: http://localhost:{args.port}/health")
    print()
    print("Services:")
    print(f"   - Database: SQLite (auth_simple)")
    print(f"   - Cache: Memory fallback (Redis unavailable)")
    print(f"   - Strategy Execution: MockMarketDataProvider")
    print()
    print("Press CTRL+C to stop the server")
    print("=" * 60)
    print()

    try:
        uvicorn.run(
            "src.api.main:app",
            host=args.host,
            port=args.port,
            reload=False,  # 不使用熱重載以避免緩存問題
            log_level="info",
            access_log=True
        )
    except KeyboardInterrupt:
        print(f"\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Server error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
