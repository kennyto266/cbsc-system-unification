#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple Market Check - 簡化市場時間檢查
"""

import os
import sys
import asyncio
from datetime import datetime, timezone, timedelta

async def simple_market_check():
    try:
        import futu as ft

        print("=== Market Hours Check ===")
        print("=" * 50)
        
        # Get current time in Hong Kong (UTC+8)
        now_utc = datetime.now(timezone.utc)
        now_hk = now_utc + timedelta(hours=8)
        
        print(f"Current Hong Kong Time: {now_hk.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Day of Week: {now_hk.strftime('%A')}")
        
        # Check if weekend
        is_weekend = now_hk.weekday() >= 5  # Saturday=5, Sunday=6
        print(f"Weekend: {'Yes' if is_weekend else 'No'}")
        
        # HK market hours: 09:30-16:00 HKT
        hk_open = now_hk.replace(hour=9, minute=30, second=0, microsecond=0)
        hk_close = now_hk.replace(hour=16, minute=0, second=0, microsecond=0)
        hk_is_trading = not is_weekend and hk_open <= now_hk <= hk_close
        
        print(f"\nHong Kong Market:")
        print(f"  Trading Hours: 09:30-16:00 HKT")
        print(f"  Current Status: {'TRADING' if hk_is_trading else 'CLOSED'}")
        
        if hk_is_trading:
            print(f"  ✅ MARKET IS OPEN - Good for testing!")
        else:
            print(f"  ❌ MARKET IS CLOSED")
            print(f"  Time until open: {hk_open - now_hk}")
            print(f"  Next open: {hk_open.strftime('%Y-%m-%d %H:%M HKT')}")
        
        # Check Futu API status
        print(f"\nFutu API Status:")
        try:
            quote_ctx = ft.OpenQuoteContext(host='127.0.0.1', port=1130)
            
            ret, state = quote_ctx.get_global_state()
            if ret == ft.RET_OK:
                print(f"  Quote Login: {state.get('qot_logined', False)}")
                print(f"  Trade Login: {state.get('trd_logined', False)}")
                print(f"  Market HK: {state.get('market_hk', 'Unknown')}")
                print(f"  Market US: {state.get('market_us', 'Unknown')}")
                
                if state.get('market_hk') == 'CLOSED' and not hk_is_trading:
                    print(f"  ✅ API reports HK market as CLOSED (matches time)")
                elif state.get('market_hk') == 'CLOSED' and hk_is_trading:
                    print(f"  ⚠️  API says CLOSED but time says OPEN - check time zone")
                elif state.get('market_hk') == 'OPEN' and hk_is_trading:
                    print(f"  ✅ API reports OPEN (matches time)")
                else:
                    print(f"  ⚠️  API status and time analysis mismatch")
            
            quote_ctx.close()
            
        except Exception as e:
            print(f"  API check failed: {e}")
        
        # Recommendations
        print(f"\nRecommendations:")
        if hk_is_trading:
            print("  ✅ Good time for API testing")
            print("  Trading functions should work better during market hours")
        else:
            print("  ❌ Try again during HK market hours (09:30-16:00 HKT)")
            print("  Some functions may be restricted outside trading hours")
            print("  Error code -1 is common during market closure")
        
        print(f"\nKey Insight: Error code -1 is often related to:")
        print(f"1. Market closure restrictions")
        print(f"2. Non-trading hour limitations")
        print(f"3. Server maintenance periods")
        print(f"4. API rate limiting outside peak hours")
        
        return {
            'hk_trading': hk_is_trading,
            'is_weekend': is_weekend,
            'current_time_hk': now_hk,
            'hk_open': hk_open,
            'hk_close': hk_close
        }
        
    except Exception as e:
        print(f"Market check failed: {e}")
        return None

if __name__ == "__main__":
    result = asyncio.run(simple_market_check())
    
    print(f"\n" + "=" * 50)
    if result:
        if not result['hk_trading']:
            print("CONCLUSION: Market closure likely cause of error code -1")
            print(f"Next HK trading session: {result['hk_open'].strftime('%Y-%m-%d %H:%M')} HKT")
        else:
            print("CONCLUSION: Market is open - good time for testing")
    else:
        print("Could not determine market status")