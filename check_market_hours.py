#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Check Market Hours - 檢查當前市場時間和交易時間
"""

import os
import sys
import asyncio
from datetime import datetime, timezone, timedelta

# Set environment variables
os.environ['PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION'] = 'python'
sys.path.append(r'C:\Users\Penguin8n\CODEX--\.venv\Lib\site-packages')

API_PORT = 1130
HOST = '127.0.0.1'

async def check_market_hours():
    try:
        import futu as ft

        print("=== Check Market Hours ===")
        print("Analyzing current market conditions")
        print("=" * 60)
        
        # Get current time in different timezones
        now_utc = datetime.now(timezone.utc)
        now_hk = now_utc + timedelta(hours=8)  # Hong Kong (UTC+8)
        now_us = now_utc - timedelta(hours=5)  # US Eastern (UTC-5 for EST)
        now_us_west = now_utc - timedelta(hours=8)  # US West (UTC-8 for PST)
        
        print(f"\nCURRENT TIME ANALYSIS:")
        print(f"UTC Time:    {now_utc.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Hong Kong:  {now_hk.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"US Eastern: {now_us.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"US Pacific: {now_us_west.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Day of week
        day_of_week = now_hk.strftime('%A')
        print(f"Day of Week: {day_of_week}")
        
        # Check if it's weekend
        is_weekend = now_hk.weekday() >= 5  # Saturday=5, Sunday=6
        print(f"Weekend: {'Yes' if is_weekend else 'No'}")
        
        # Market hours analysis
        print(f"\nMARKET HOURS ANALYSIS:")
        
        # Hong Kong Market
        hk_open = now_hk.replace(hour=9, minute=30, second=0, microsecond=0)
        hk_close = now_hk.replace(hour=16, minute=0, second=0, microsecond=0)
        hk_is_trading = not is_weekend and hk_open <= now_hk <= hk_close
        
        print(f"HK Market:")
        print(f"  Trading Hours: 09:30-16:00 HKT")
        print(f"  Current Status: {'TRADING' if hk_is_trading else 'CLOSED'}")
        print(f"  Next Open: {hk_open.strftime('%Y-%m-%d %H:%M')} HKT")
        print(f"  Next Close: {hk_close.strftime('%Y-%m-%d %H:%M')} HKT")
        
        # US Market (Eastern Time)
        us_open = now_us.replace(hour=9, minute=30, second=0, microsecond=0)
        us_close = now_us.replace(hour=16, minute=0, second=0, microsecond=0)
        us_is_trading = not is_weekend and us_open <= now_us <= us_close
        
        print(f"\nUS Market:")
        print(f"  Trading Hours: 09:30-16:00 ET")
        print(f"  Current Status: {'TRADING' if us_is_trading else 'CLOSED'}")
        print(f"  Next Open: {us_open.strftime('%Y-%m-%d %H:%M')} ET")
        print(f"  Next Close: {us_close.strftime('%Y-%m-%d %H:%M')} ET")
        
        # Futu API testing
        print(f"\nFUTU API STATUS:")
        try:
            quote_ctx = ft.OpenQuoteContext(host=HOST, port=API_PORT)
            
            # Get global state
            ret, state = quote_ctx.get_global_state()
            if ret == ft.RET_OK:
                print(f"  Server Version: {state.get('server_ver', 'Unknown')}")
                print(f"  Quote Login: {state.get('qot_logined', False)}")
                print(f"  Trade Login: {state.get('trd_logined', False)}")
                print(f"  Market HK: {state.get('market_hk', 'Unknown')}")
                print(f"  Market US: {state.get('market_us', 'Unknown')}")
                print(f"  Local Time: {state.get('local_time', 'Unknown')}")
            else:
                print(f"  Global state query failed: {ret}")
            
            quote_ctx.close()
            
        except Exception as e:
            print(f"  Futu API check failed: {e}")
        
        # Recommendations
        print(f"\nTRADING TIME RECOMMENDATIONS:")
        print(f"=" * 50)
        
        if hk_is_trading:
            print("✅ Hong Kong market is OPEN - Good time for HK trading")
        else:
            print("❌ Hong Kong market is CLOSED")
            print("   Next HK trading: Tomorrow 09:30-16:00 HKT")
        
        if us_is_trading:
            print("✅ US market is OPEN - Good time for US trading")
        else:
            print("❌ US market is CLOSED")
            print("   Next US trading: Tomorrow 09:30-16:00 ET")
        
        if is_weekend:
            print("❌ It's weekend - Markets closed")
            print("   Next trading: Monday")
        else:
            print("✅ It's weekday - Markets should be open during hours")
        
        # Calculate next testing times
        print(f"\nOPTIMAL TESTING TIMES:")
        print(f"=" * 50)
        
        tomorrow = now_hk + timedelta(days=1)
        while tomorrow.weekday() >= 5:  # Skip to Monday
            tomorrow += timedelta(days=1)
        
        next_hk_open = tomorrow.replace(hour=9, minute=30, second=0, microsecond=0)
        next_hk_close = tomorrow.replace(hour=16, minute=0, second=0, microsecond=0)
        
        print(f"HK Market Testing:")
        print(f"  Start: {next_hk_open.strftime('%Y-%m-%d %H:%M HKT')}")
        print(f"  End:   {next_hk_close.strftime('%Y-%m-%d %H:%M HKT')}")
        print(f"  Duration: 6.5 hours")
        
        # US time conversion for HK trading hours
        us_hk_open = next_hk_open - timedelta(hours=13)  # HK is 13 hours ahead of US Eastern
        us_hk_close = next_hk_close - timedelta(hours=13)
        
        print(f"US Market Testing (during HK hours):")
        print(f"  HK 09:30 = US {us_hk_open.strftime('%H:%M ET (previous day)')}")
        print(f"  HK 16:00 = US {us_hk_close.strftime('%H:%M ET (previous day)'}")
        
        return {
            'hk_trading': hk_is_trading,
            'us_trading': us_is_trading,
            'is_weekend': is_weekend,
            'next_hk_open': next_hk_open,
            'next_hk_close': next_hk_close,
            'current_time_hk': now_hk
        }
        
    except Exception as e:
        print(f"Market hours check failed: {e}")
        return None

if __name__ == "__main__":
    result = asyncio.run(check_market_hours())
    
    print(f"\n" + "=" * 60)
    if result:
        print("MARKET HOURS ANALYSIS COMPLETE")
        print("\nKEY INSIGHTS:")
        print("1. Non-trading hours may restrict certain API functions")
        print("2. Error code -1 is common during market closure")
        print("3. Try again during HK market hours (09:30-16:00 HKT)")
        print("4. Some functions may work during US market hours")
        
        if not result['hk_trading'] and not result['us_trading']:
            print(f"\nCURRENT STATUS: BOTH MARKETS CLOSED")
            print(f"Recommended to test again during market hours")
            print(f"HK Market: {result['next_hk_open'].strftime('%Y-%m-%d %H:%M')} HKT")
            print(f"US Market: {result['next_hk_open'].strftime('%Y-%m-%d %H:%M')} ET")
    else:
        print("CURRENT STATUS: AT LEAST ONE MARKET OPEN")
        print("This may be a good time for testing!")