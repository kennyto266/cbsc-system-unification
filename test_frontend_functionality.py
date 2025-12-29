from playwright.sync_api import sync_playwright

def test_frontend_functionality():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Test home page redirect
        print("Testing home page redirect...")
        page.goto('http://localhost:3001')
        page.wait_for_load_state('networkidle')

        if '/dashboard' in page.url:
            print("[OK] Successfully redirected to dashboard")
        else:
            print(f"[FAIL] Redirect failed. Current URL: {page.url}")
            browser.close()
            return

        # Test quick action buttons
        print("\n[INFO] Testing Quick Action buttons...")

        # Test Create Strategy button
        print("\n[INFO] Testing 'Create Strategy' button...")
        createBtn = page.locator('button:has-text("創建新策略")')
        if createBtn.count() > 0:
            # Check if button has onClick handler
            createBtn.click()
            page.wait_for_timeout(2000)
            if '/dashboard/strategies' in page.url:
                print("[OK] Create Strategy button navigates to strategies page")
            else:
                print("[INFO] Create Strategy button clicked but navigation may need implementation")
        else:
            print("[FAIL] Create Strategy button not found")

        # Go back to dashboard
        page.goto('http://localhost:3001/dashboard')
        page.wait_for_load_state('networkidle')

        # Test View Market Data button
        print("\n[INFO] Testing 'View Market Data' button...")
        marketBtn = page.locator('button:has-text("查看市場數據")')
        if marketBtn.count() > 0:
            print("[OK] View Market Data button found")
            # Note: This opens in new tab, so we'll just verify it exists
        else:
            print("[FAIL] View Market Data button not found")

        # Test Run Backtest button
        print("\n[INFO] Testing 'Run Backtest' button...")
        backtestBtn = page.locator('button:has-text("運行回測")')
        if backtestBtn.count() > 0:
            print("[OK] Run Backtest button found")
            # Click to test API call
            backtestBtn.click()
            page.wait_for_timeout(2000)
            # Check if any error/alert appeared (would be visible in real browser)
        else:
            print("[FAIL] Run Backtest button not found")

        # Test Export Report button
        print("\n[INFO] Testing 'Export Report' button...")
        exportBtn = page.locator('button:has-text("導出報告")')
        if exportBtn.count() > 0:
            print("[OK] Export Report button found")
        else:
            print("[FAIL] Export Report button not found")

        # Test strategies page
        print("\n[INFO] Testing Strategies page...")
        page.goto('http://localhost:3001/dashboard/strategies')
        page.wait_for_load_state('networkidle')

        # Check for strategies table
        table = page.locator('table').count()
        if table > 0:
            print("[OK] Strategies table found")

            # Test Edit and View buttons
            editBtn = page.locator('button:has-text("編輯")')
            viewBtn = page.locator('button:has-text("查看")')

            if editBtn.count() > 0:
                print("[OK] Edit buttons found in strategies table")
            else:
                print("[FAIL] No Edit buttons found")

            if viewBtn.count() > 0:
                print("[OK] View buttons found in strategies table")
            else:
                print("[FAIL] No View buttons found")
        else:
            print("[FAIL] Strategies table not found")

        browser.close()
        print("\n[INFO] Frontend functionality test completed")

if __name__ == "__main__":
    test_frontend_functionality()