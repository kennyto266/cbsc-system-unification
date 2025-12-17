#!/usr/bin/env python
"""
Test WebSocket connection between frontend and backend
"""
import webbrowser
import time
import threading
import requests
from pathlib import Path

def check_backend_health():
    """Check if backend is running"""
    try:
        response = requests.get("http://localhost:3004/", timeout=5)
        return response.status_code == 200
    except:
        return False

def main():
    print("WebSocket Frontend Connection Test")
    print("=" * 50)

    # Check if backend is running
    print("\n1. Checking backend server status...")
    if check_backend_health():
        print("[OK] Backend server is running")
    else:
        print("[FAIL] Backend server is not running, please start it first:")
        print("   cd backend && python main.py")
        return

    # Check if frontend is running
    print("\n2. Checking frontend server status...")
    try:
        response = requests.get("http://localhost:3002", timeout=5)
        if response.status_code == 200:
            print("[OK] Frontend server is running (port 3002)")
        else:
            print("[WARN] Frontend server response is abnormal")
    except:
        print("[FAIL] Frontend server is not running, please start it first:")
        print("   cd square-ui-frontend && npm run dev")

    # Open test page
    print("\n3. Opening WebSocket test page...")
    test_file = Path(__file__).parent / "test-frontend-websocket.html"
    test_file = test_file.absolute()

    # Use file:// protocol
    url = f"file:///{test_file}".replace("\\", "/")

    print(f"   Opening: {url}")
    webbrowser.open(url)

    print("\nTest Instructions:")
    print("1. Click 'Connect' button to connect to WebSocket server")
    print("2. Click various channel buttons to subscribe to data")
    print("3. Observe real-time data received")
    print("\nAvailable channels:")
    print("- strategy_performance: Strategy performance data")
    print("- market_data: Market data")
    print("- hibor_rates: HIBOR rates")
    print("- cbsc_contracts: CBSC contracts")
    print("- government_data: Government data")
    print("- system_status: System status")

    print("\n[OK] Test page opened, please test in browser")

if __name__ == "__main__":
    main()